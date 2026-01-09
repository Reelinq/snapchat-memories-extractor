from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config.main import Config
from src.downloader.download_task import DownloadTask
from src.models import Memory
from src.memories_repository import MemoriesRepository
from src.logger.log import log


class MemoryDownloader:
    def run(self) -> None:
        completed_downloads_count = 0
        completed_indices = set()
        future_download_tasks = self._gather_future_download_tasks()

        if not future_download_tasks:
            log("No items to download.", "info")
            return

        for future in as_completed(future_download_tasks):
            index, _ = future_download_tasks[future]
            completed_downloads_count += 1

            file_path, download_succeeded = future.result()

            self._prune_memory_item(index, file_path, download_succeeded)
            completed_indices.add(index)
            self._update_ui()
            self._log_processed_indices(completed_indices)


    def _gather_future_download_tasks(self):
        download_tasks = self._gather_download_tasks()
        max_workers = Config.from_args().cli_options['max_concurrent_downloads']
        executor = ThreadPoolExecutor(max_workers=max_workers)

        # Use dictonary becaude otherwsie index gets lost in 'as_completed'
        futures = {}

        for index, memory in enumerate(download_tasks):
            future = executor.submit(DownloadTask, memory)
            futures[future] = (index, memory)

        return futures


    @staticmethod
    def _gather_download_tasks():
        download_tasks = []
        raw_memory_items = MemoriesRepository(Config.json_path).get_raw_items()

        for item in raw_memory_items:
            memory = Memory.model_validate(item)
            download_tasks.append(memory)

        return download_tasks


    def _prune_memory_item(self, index: int, file_path: Path, download_succeeded: bool) -> None:
        if not download_succeeded:
            return

        file_size_mb = self._convert_file_size(file_path)
        MemoriesRepository().prune(index)
        log(f"Downloaded item {file_path.name}. File size: {file_size_mb:.2f} MB. Successfully pruned from json.", "info")


    @staticmethod
    def _convert_file_size(file_path: Path) -> float:
        return file_path.stat().st_size / (1024 * 1024)


    @staticmethod
    def _update_ui():
        # TODO: Update UI in a thread-safe manner
        """with self.stats.lock:
            if download_succeeded:
                self.stats.successful_downloads_count += 1
                self.successfully_processed_indices.add(index)
                self.pending_prune_indices.add(index)
            else:
                self.stats.failed_downloads_count += 1

            current_successful = self.stats.successful_downloads_count
            current_failed = self.stats.failed_downloads_count

            total_files_count = len(MemoriesRepository(Config.json_path).get_raw_items())

            update_progress_threadsafe(
                completed_downloads_count,
                total_files_count,
                current_successful,
                current_failed,
                time.time(),
                memory.filename_with_ext,
                self.ui_shown
            )"""


    @staticmethod
    def _log_processed_indices(indices: set[int]) -> None:
        if indices and len(indices) % 10 == 0:
            log(f"Successfully processed {len(indices)} items so far", "debug")
