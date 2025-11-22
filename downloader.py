import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from config import Config
from models import Memory
from services.download_service import DownloadService
from ui.display import print_status, clear_lines, print_error_summary

class MemoryDownloader:
    def __init__(self, config: Config):
        self.config = config
        self.download_service = DownloadService(config)

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


    def _prune_json(self, data: Dict, raw_items: List, success_indices: set) -> None:
        if not success_indices:
            return

        remaining = [itm for i, itm in enumerate(raw_items) if i not in success_indices]
        data['Saved Media'] = remaining

        with open(self.config.json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
