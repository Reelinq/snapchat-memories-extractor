import time
from typing import List, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging
from config import Config
from models import Memory
from memory_repository import MemoryRepository
from services.download_service import DownloadService
from services.jxl_converter import JXLConverter
from ui.display import print_status, clear_lines
from logger import get_logger

class MemoryDownloader:
    def __init__(self, config: Config):
        self.config = config
        self.repository = MemoryRepository(config.json_path)

        # Thread synchronization
        self.stats_lock = threading.Lock()
        self.display_lock = threading.Lock()

        self.download_service = DownloadService(config, self.stats_lock)
        self.logger = get_logger("snapchat_extractor")

        # Reusable ThreadPoolExecutor (avoids creation overhead across retry attempts)
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_downloads)

        # Statistics
        self.successful = 0
        self.failed = 0
        self.total_bytes = 0
        self.start_time = 0.0
        self.errors: List[Dict[str, str]] = []
        self.ui_shown = False

        # Batch pruning state
        self.pending_prune_indices: Set[int] = set()
        self.last_prune_count = 0

        # Interrupt state
        self._interrupted = False

    def _suppress_console_logging(self, suppress: bool = True):
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream.name == '<stdout>':
                handler.setLevel(logging.CRITICAL if suppress else logging.INFO)


    def close(self) -> None:
        # Release resources: shared HTTP sessions and ThreadPoolExecutor
        self.download_service.close()
        # Don't wait for threads if interrupted; exit immediately
        wait = not self._interrupted
        self.executor.shutdown(wait=wait)

    def _batch_prune_if_needed(self, force: bool = False) -> None:
        should_prune = (
            force and self.pending_prune_indices
        ) or (
            self.config.prune_batch_size > 0
            and len(self.pending_prune_indices) >= self.config.prune_batch_size
        )

        if should_prune:
            self.repository.prune(self.pending_prune_indices)
            self.last_prune_count = len(self.pending_prune_indices)
            self.logger.debug(f"Batched prune: removed {self.last_prune_count} items from JSON")
            self.pending_prune_indices.clear()


    def run(self) -> None:
        for run_attempt in range(self.config.max_attempts):
            if run_attempt > 0:
                self.logger.info(f"Starting attempt {run_attempt + 1}/{self.config.max_attempts}...")
                time.sleep(2)

                self.successful = 0
                self.failed = 0
                self.total_bytes = 0
                self.errors.clear()
                self.ui_shown = False

            self._run_download_batch()

            if self.failed == 0 or run_attempt == self.config.max_attempts - 1:
                break


    def _run_download_batch(self) -> None:
        raw_items = self.repository.get_raw_items()
        success_indices: Set[int] = set()
        total_files = len(raw_items)
        self.start_time = time.time()
        completed_count = 0

        # Reset batch state
        self.pending_prune_indices.clear()
        self.last_prune_count = 0

        # Suppress console logging during UI updates
        self._suppress_console_logging(True)

        # Create memory objects with their indices
        tasks = [(index, Memory.model_validate(item)) for index, item in enumerate(raw_items)]

        # Reuse the shared executor (avoids creation overhead on retries)
        future_to_task = {
            self.executor.submit(self._download_task, index, memory): (index, memory)
            for index, memory in tasks
        }

        try:
            # Process completed tasks
            for future in as_completed(future_to_task):
                index, memory = future_to_task[future]
                completed_count += 1

                try:
                    success = future.result()

                    with self.stats_lock:
                        if success:
                            self.successful += 1
                            success_indices.add(index)
                            self.pending_prune_indices.add(index)
                        else:
                            self.failed += 1

                        # Capture current stats for display
                        current_successful = self.successful
                        current_failed = self.failed

                    # Batch prune if threshold reached
                    self._batch_prune_if_needed()

                    # Update progress display outside the lock
                    with self.display_lock:
                        if self.ui_shown:
                            clear_lines(10)
                        self.ui_shown = True
                        print_status(
                            completed_count,
                            total_files,
                            current_successful,
                            current_failed,
                            time.time() - self.start_time,
                            f"Downloading: {memory.filename_with_ext}"
                        )

                    # Periodically log but don't clear success_indices
                    # We need to track all indices for final prune
                    if len(success_indices) % 10 == 0 and success_indices:
                        self.logger.debug(f"Successfully processed {len(success_indices)} items so far")

                except Exception as e:
                    with self.stats_lock:
                        self.failed += 1
                        current_failed = self.failed
                        self.errors.append({
                            'filename': memory.filename_with_ext,
                            'url': memory.media_download_url,
                            'code': 'ERR'
                        })

                    # Update progress for failed download
                    with self.display_lock:
                        if self.ui_shown:
                            clear_lines(10)
                        self.ui_shown = True
                        print_status(
                            completed_count,
                            total_files,
                            self.successful,
                            current_failed,
                            time.time() - self.start_time,
                            f"Downloading: {memory.filename_with_ext}"
                        )

        except KeyboardInterrupt:
            self.logger.warning("Download interrupted by user")
            self._interrupted = True
            # Don't wait for executor; cancel pending tasks and exit
            self.executor.shutdown(wait=False, cancel_futures=True)
            # Force prune pending items on interrupt
            self._batch_prune_if_needed(force=True)
            # Convert any JPEGs that didn't complete conversion before exit
            self._convert_remaining_jpegs_on_interrupt()
            raise

        # Final prune
        self._batch_prune_if_needed(force=True)

        clear_lines(10)
        total_time = time.time() - self.start_time
        print_status(total_files, total_files, self.successful, self.failed, total_time, "✅ COMPLETE!")

        # Re-enable console logging before error reporting
        self._suppress_console_logging(False)

        # Log all errors to JSON
        for error in self.errors:
            code = error.get('code', 'ERR')
            filename = error['filename']
            url = error.get('url', '')
            self.logger.error(f"Download failed: {filename} (code: {code})", extra={"extra_data": {"code": code, "filename": filename, "url": url}})

        if self.failed > 0:
            self.logger.info(f"Check logs for details on {self.failed} failed downloads")

    def _backfill_existing_jpegs_to_jxl(self) -> None:
        if not self.config.convert_to_jxl:
            return

        jpeg_paths = list(self.config.downloads_folder.glob('*.jpg')) + list(self.config.downloads_folder.glob('*.jpeg'))
        if not jpeg_paths:
            return

        converted_count = 0
        for jpg_path in jpeg_paths:
            # Skip if a JXL already exists
            jxl_path = jpg_path.with_suffix('.jxl')
            if jxl_path.exists():
                continue

            if not JXLConverter.is_convertible_image(jpg_path):
                continue

            new_path = JXLConverter.convert_to_jxl(jpg_path)
            if new_path.suffix.lower() == '.jxl':
                converted_count += 1

        if converted_count > 0:
            print(f"🔄 Converted {converted_count} leftover JPEG(s) to JPGXL format")
            self.logger.info(f"Backfilled {converted_count} JPEG(s) to JPGXL format")

    def _convert_remaining_jpegs_on_interrupt(self) -> None:
        if not self.config.convert_to_jxl:
            return

        jpeg_paths = list(self.config.downloads_folder.glob('*.jpg')) + list(self.config.downloads_folder.glob('*.jpeg'))
        if not jpeg_paths:
            return

        print(f"\n🔄 Converting {len(jpeg_paths)} JPEG(s) to JPGXL before exit...")
        converted_count = 0

        for jpg_path in jpeg_paths:
            # Skip if a JXL already exists
            jxl_path = jpg_path.with_suffix('.jxl')
            if jxl_path.exists():
                continue

            if not JXLConverter.is_convertible_image(jpg_path):
                continue

            new_path = JXLConverter.convert_to_jxl(jpg_path)
            if new_path.suffix.lower() == '.jxl':
                converted_count += 1

        if converted_count > 0:
            print(f"✅ Converted {converted_count} JPEG(s) to JPGXL")
            self.logger.info(f"Post-interrupt conversion: {converted_count} JPEG(s) to JPGXL")


    def _download_task(self, index: int, memory: Memory) -> bool:
        try:
            if self.config.strict_location and memory.location_coords is None:
                with self.stats_lock:
                    self.errors.append({
                        'filename': memory.filename_with_ext,
                        'url': memory.media_download_url,
                        'code': 'LOC'
                    })
                self.logger.warning(
                    "Skipping download due to missing location: %s",
                    memory.filename_with_ext
                )
                return False

            success = self.download_service.download_and_process(memory)

            # Merge errors from download service
            with self.stats_lock:
                if self.download_service.errors:
                    self.errors.extend(self.download_service.errors)
                    self.download_service.errors.clear()
                self.total_bytes += self.download_service.total_bytes
                self.download_service.total_bytes = 0

            return success
        except Exception as e:
            with self.stats_lock:
                    self.errors.append({
                        'filename': memory.filename_with_ext,
                        'url': memory.media_download_url,
                        'code': 'ERR'
                    })
            return False
