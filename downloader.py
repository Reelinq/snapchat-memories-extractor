import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import requests
from config import Config
from models import Memory
from filename_resolver import FileNameResolver
from zip_processor import ZipProcessor
from metadata_writers import ImageMetadataWriter, VideoMetadataWriter
from ui import print_status, update_progress, clear_lines, print_error_summary

class MemoryDownloader:
    def __init__(self, config: Config):
        self.config = config
        self.filename_resolver = FileNameResolver(config.downloads_folder)
        self.content_processor = ZipProcessor()

        # Statistics
        self.successful = 0
        self.failed = 0
        self.total_bytes = 0
        self.start_time = 0.0
        self.errors: List[Dict[str, str]] = []

        # Thread synchronization
        self.stats_lock = threading.Lock()
        self.json_lock = threading.Lock()
        self.display_lock = threading.Lock()
        self.ui_shown = False


    def run(self) -> None:
        for run_attempt in range(self.config.max_attempts):
            if run_attempt > 0:
                print(f"\n🔄 Starting attempt {run_attempt + 1}/{self.config.max_attempts}...\n")
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
        data = self._load_json()
        raw_items = data.get('Saved Media', [])
        success_indices = set()
        total_files = len(raw_items)
        self.start_time = time.time()
        completed_count = 0

        # Create memory objects with their indices
        tasks = [(index, Memory.model_validate(item)) for index, item in enumerate(raw_items)]

        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_downloads) as executor:
            future_to_task = {
                executor.submit(self._download_task, index, memory): (index, memory)
                for index, memory in tasks
            }

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
                        else:
                            self.failed += 1

                        # Capture current stats for display
                        current_successful = self.successful
                        current_failed = self.failed

                    # Update progress display outside the lock
                    with self.display_lock:
                        if self.ui_shown:
                            clear_lines(11)
                        self.ui_shown = True
                        print_status(
                            completed_count,
                            total_files,
                            current_successful,
                            current_failed,
                            time.time() - self.start_time,
                            f"Downloading: {memory.filename_with_ext}"
                        )

                    # Periodically prune the JSON file
                    if len(success_indices) % 10 == 0:
                        with self.json_lock:
                            self._prune_json(data, raw_items, success_indices)

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
                            clear_lines(11)
                        self.ui_shown = True
                        print_status(
                            completed_count,
                            total_files,
                            self.successful,
                            current_failed,
                            time.time() - self.start_time,
                            f"Downloading: {memory.filename_with_ext}"
                        )

        # Final prune
        with self.json_lock:
            self._prune_json(data, raw_items, success_indices)

        clear_lines(10)
        total_time = time.time() - self.start_time
        print_status(total_files, total_files, self.successful, self.failed, total_time, "✅ COMPLETE!")

        if self.errors:
            print_error_summary(self.errors)


    def _load_json(self) -> Dict:
        with open(self.config.json_path, 'r', encoding='utf-8') as file:
            return json.load(file)


    def _download_task(self, index: int, memory: Memory) -> bool:
        try:
            return self._download_and_process(memory)
        except Exception as e:
            with self.stats_lock:
                self.errors.append({
                    'filename': memory.filename_with_ext,
                    'url': memory.media_download_url,
                    'code': 'ERR'
                })
            return False


    def _download_and_process(self, memory: Memory) -> bool:
        try:
            response = requests.get(memory.media_download_url, timeout=self.config.request_timeout)

            # Check status code and extract it before raising
            if response.status_code >= 400:
                with self.stats_lock:
                    self.errors.append({
                        'filename': memory.filename_with_ext,
                        'url': memory.media_download_url,
                        'code': str(response.status_code)
                    })
                return False

            response.raise_for_status()

            is_zip = self.content_processor.is_zip(
                response.content,
                response.headers.get('Content-Type', '')
            )

            if is_zip:
                return self._process_zip(response.content, memory)
            else:
                return self._process_regular(response.content, memory)

        except requests.exceptions.RequestException as e:
            with self.stats_lock:
                self.errors.append({
                    'filename': memory.filename_with_ext,
                    'url': memory.media_download_url,
                    'code': 'NET'
                })
            return False
        except Exception as e:
            with self.stats_lock:
                self.errors.append({
                    'filename': memory.filename_with_ext,
                    'url': memory.media_download_url,
                    'code': 'ERR'
                })
            return False


    def _process_zip(self, content: bytes, memory: Memory) -> bool:
        filepath = None
        try:
            media_bytes, extension, overlay_png = self.content_processor.extract_media_from_zip(
                content,
                extract_overlay=self.config.apply_overlay
            )

            # Apply overlay if enabled
            if self.config.apply_overlay and overlay_png:
                is_image = memory.media_type == "Image"

                if is_image:
                    media_bytes = self.content_processor.apply_overlay_to_image(media_bytes, overlay_png)
                else:
                    # For videos, apply overlay directly to the output path
                    filepath = self.config.downloads_folder / f"{memory.filename}{extension}"
                    filepath = self.filename_resolver.resolve_unique_path(filepath)

                    self.content_processor.apply_overlay_to_video(
                        media_bytes,
                        overlay_png,
                        filepath,
                        self.config.ffmpeg_timeout
                    )

            if filepath is None:
                filepath = self.config.downloads_folder / f"{memory.filename}{extension}"
                filepath = self.filename_resolver.resolve_unique_path(filepath)
                filepath.write_bytes(media_bytes)

            # Write metadata for all files
            is_image = memory.media_type == "Image"
            writer = ImageMetadataWriter(memory) if is_image else VideoMetadataWriter(memory, self.config.ffmpeg_timeout)
            writer.write_metadata(filepath)

            with self.stats_lock:
                self.total_bytes += filepath.stat().st_size
            return True

        except Exception as e:
            if filepath:
                filepath.unlink(missing_ok=True)
            with self.stats_lock:
                self.errors.append({
                    'filename': memory.filename_with_ext,
                    'url': memory.media_download_url,
                    'code': 'ZIP'
                })
            return False


    def _process_regular(self, content: bytes, memory: Memory) -> bool:
        filepath = self.config.downloads_folder / memory.filename_with_ext
        filepath = self.filename_resolver.resolve_unique_path(filepath)

        try:
            filepath.write_bytes(content)

            is_image = memory.media_type == "Image"
            writer = ImageMetadataWriter(memory) if is_image else VideoMetadataWriter(memory, self.config.ffmpeg_timeout)
            writer.write_metadata(filepath)

            with self.stats_lock:
                self.total_bytes += filepath.stat().st_size
            return True

        except Exception as e:
            filepath.unlink(missing_ok=True)
            with self.stats_lock:
                self.errors.append({
                    'filename': memory.filename_with_ext,
                    'url': memory.media_download_url,
                    'code': 'FILE'
                })
            return False


    def _prune_json(self, data: Dict, raw_items: List, success_indices: set) -> None:
        if not success_indices:
            return

        remaining = [itm for i, itm in enumerate(raw_items) if i not in success_indices]
        data['Saved Media'] = remaining

        with open(self.config.json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
