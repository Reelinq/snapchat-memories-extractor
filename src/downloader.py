import time
from typing import List, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging
from src.config.main import Config
from src.models import Memory
from src.repositories.memories_repository import MemoriesRepository
from src.services.download_service import DownloadService
from src.services.jxl_converter import JXLConverter
from src.ui.display import print_status, clear_lines, update_progress
from src.logger import get_logger
from src.error_handling import handle_errors, handle_batch_errors, LocationMissingError, safe_future_result


class MemoryDownloader:
    def __init__(self, config: Config):
        self.config = config
        self.memories_repository = MemoriesRepository(config.json_path)

        self.stats_lock = threading.Lock()
        self.display_lock = threading.Lock()

        self.download_service = DownloadService(config, self.stats_lock)
        self.logger = get_logger("snapchat_extractor")

        self.executor = ThreadPoolExecutor(
            max_workers=config.cli_options['max_concurrent_downloads'])

        self.successful_downloads_count = 0
        self.failed_downloads_count = 0
        self.total_bytes = 0
        self.start_time = 0.0
        self.errors: List[Dict[str, str]] = []
        self.ui_shown = False

        self.pending_prune_indices: Set[int] = set()

        self._interrupted = False

    def _suppress_console_logging(self, suppress: bool = True):
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream.name == '<stdout>':
                handler.setLevel(logging.CRITICAL if suppress else logging.INFO)

    def close(self) -> None:
        self.download_service.close()
        should_wait_for_shutdown = not self._interrupted
        self.executor.shutdown(wait=should_wait_for_shutdown)

    def _batch_prune_if_needed(self) -> None:
        if self.pending_prune_indices:
            indices_to_prune = set(self.pending_prune_indices)
            raw_items = self.repository.get_raw_items()
            pruned_filenames = [Memory.model_validate(
                raw_items[i]).filename_with_ext for i in indices_to_prune if i < len(raw_items)]
            self.repository.prune(indices_to_prune)
            for fname in pruned_filenames:
                self.logger.info(f"Successfully pruned {fname} from JSON.")
            self.pending_prune_indices.clear()

    def run(self) -> None:
        for current_attempt_number in range(self.config.cli_options['max_attempts']):
            if current_attempt_number > 0:
                self.logger.info(
                    f"Starting attempt {current_attempt_number + 1}/{self.config.cli_options['max_attempts']}...")
                time.sleep(2)

                self.successful_downloads_count = 0
                self.failed_downloads_count = 0
                self.total_bytes = 0
                self.errors.clear()
                self.ui_shown = False

            self._run_download_batch()

            if self.failed_downloads_count == 0 or current_attempt_number == self.config.cli_options['max_attempts'] - 1:
                break

    @handle_batch_errors(cleanup_method='_batch_prune_if_needed')
    def _run_download_batch(self) -> None:
        raw_memory_items = self.memories_repository.get_raw_items()
        successfully_processed_indices: Set[int] = set()
        total_files_count = len(raw_memory_items)
        self.start_time = time.time()
        completed_downloads_count = 0

        self.pending_prune_indices.clear()

        self._suppress_console_logging(True)

        download_tasks = [(index, Memory.model_validate(item))
                          for index, item in enumerate(raw_memory_items)]

        future_to_download_task_mapping = {
            self.executor.submit(self._download_task, index, memory): (index, memory)
            for index, memory in download_tasks
        }

        for future in as_completed(future_to_download_task_mapping):
            index, memory = future_to_download_task_mapping[future]
            completed_downloads_count += 1

            result = safe_future_result(
                future, default_on_error=(None, False))
            file_path, download_succeeded = result

            if download_succeeded and file_path and file_path.exists():
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                self.memories_repository.prune(index)
                self.logger.info(
                    f"Downloaded item {file_path.name}. File size: {file_size_mb:.2f} MB. Successfully pruned from json."
                )

            with self.stats_lock:
                if download_succeeded:
                    self.successful_downloads_count += 1
                    successfully_processed_indices.add(index)
                    self.pending_prune_indices.add(index)
                else:
                    self.failed_downloads_count += 1

                current_successful = self.successful_downloads_count
                current_failed = self.failed_downloads_count

            with self.display_lock:
                self.ui_shown = update_progress(
                    completed_downloads_count,
                    total_files_count,
                    current_successful,
                    current_failed,
                    self.start_time,
                    memory.filename_with_ext,
                    self.ui_shown
                )

            if len(successfully_processed_indices) % 10 == 0 and successfully_processed_indices:
                self.logger.debug(
                    f"Successfully processed {len(successfully_processed_indices)} items so far")

        # No need to log prune separately
        self._batch_prune_if_needed()

        clear_lines(10)
        total_time = time.time() - self.start_time
        print_status(total_files_count, total_files_count, self.successful_downloads_count,
                     self.failed_downloads_count, total_time, "✅ COMPLETE!")

        self._suppress_console_logging(False)

        if self.failed_downloads_count > 0:
            self.logger.info(
                f"Check logs for details on {self.failed_downloads_count} failed downloads")

    def _backfill_existing_jpegs_to_jxl(self) -> None:
        if not self.config.cli_options['convert_to_jxl']:
            return

        jpeg_file_paths = list(self.config.downloads_folder.glob(
            '*.jpg')) + list(self.config.downloads_folder.glob('*.jpeg'))
        if not jpeg_file_paths:
            return

        converted_files_count = 0
        for jpeg_file_path in jpeg_file_paths:
            jxl_file_path = jpeg_file_path.with_suffix('.jxl')
            if jxl_file_path.exists():
                continue

            if not JXLConverter.is_convertible_image(jpeg_file_path):
                continue

            converted_file_path = JXLConverter.convert_to_jxl(jpeg_file_path)
            if converted_file_path.suffix.lower() == '.jxl':
                converted_files_count += 1

        if converted_files_count > 0:
            print(
                f"🔄 Converted {converted_files_count} leftover JPEG(s) to JPGXL format")
            self.logger.info(
                f"Backfilled {converted_files_count} JPEG(s) to JPGXL format")

    def _convert_remaining_jpegs_on_interrupt(self) -> None:
        if not self.config.cli_options['convert_to_jxl']:
            return

        jpeg_file_paths = list(self.config.downloads_folder.glob(
            '*.jpg')) + list(self.config.downloads_folder.glob('*.jpeg'))
        if not jpeg_file_paths:
            return

        print(
            f"\n🔄 Converting {len(jpeg_file_paths)} JPEG(s) to JPGXL before exit...")
        converted_files_count = 0

        for jpeg_file_path in jpeg_file_paths:
            jxl_file_path = jpeg_file_path.with_suffix('.jxl')
            if jxl_file_path.exists():
                continue

            if not JXLConverter.is_convertible_image(jpeg_file_path):
                continue

            converted_file_path = JXLConverter.convert_to_jxl(jpeg_file_path)
            if converted_file_path.suffix.lower() == '.jxl':
                converted_files_count += 1

        if converted_files_count > 0:
            print(f"✅ Converted {converted_files_count} JPEG(s) to JPGXL")
            self.logger.info(
                f"Post-interrupt conversion: {converted_files_count} JPEG(s) to JPGXL")

    @handle_errors(return_on_error=False)
    def _download_task(self, index: int, memory: Memory) -> bool:
        if self.config.cli_options['strict_location']:
            if memory.location_coords is None:
                raise LocationMissingError("No location data available")

        download_succeeded = self.download_service.download_and_process(memory)

        with self.stats_lock:
            if self.download_service.errors:
                self.errors.extend(self.download_service.errors)
                self.download_service.errors.clear()

            self.total_bytes += self.download_service.total_bytes
            self.download_service.total_bytes = 0

        return download_succeeded
