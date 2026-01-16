from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import Config
from src.downloader.download_task import DownloadTask
from src.memories import *
from src.logger import log
from src.ui import StatsManager, UpdateUI


class MemoryDownloader:
    def run(self):
        completed_downloads_count = 0
        future_download_tasks = self._gather_future_download_tasks()

        if not future_download_tasks:
            log("No items to download.", "info")
            return

        for future in as_completed(future_download_tasks):
            _, memory = future_download_tasks[future]
            completed_downloads_count += 1

            file_path, download_succeeded = future.result()

            self._check_for_success(download_succeeded, memory, file_path)


    def _gather_future_download_tasks(self):
        download_tasks = self._gather_download_tasks()
        max_workers = Config.cli_options['max_concurrent_downloads']
        executor = ThreadPoolExecutor(max_workers=max_workers)

        # Use dictonary becaude otherwsie index gets lost in 'as_completed'
        futures = {}

        for index, memory in enumerate(download_tasks):
            future = executor.submit(DownloadTask(memory).run)
            futures[future] = (index, memory)

        return futures


    @staticmethod
    def _gather_download_tasks():
        download_tasks = []
        raw_memory_items = MemoriesRepository().get_raw_items()
        StatsManager.total_files = len(raw_memory_items)

        for item in raw_memory_items:
            memory = Memory.model_validate(item)
            download_tasks.append(memory)

        return download_tasks


    def _check_for_success(self, download_succeeded: bool, memory: Memory, file_path: Path) -> None:
        if download_succeeded:
            self._download_succeeded(memory, file_path)
        else:
            StatsManager.failed_downloads_count += 1
        UpdateUI().run()


    def _download_succeeded(self, memory: Memory, file_path: Path) -> None:
        self._prune_memory_item(memory, file_path)
        StatsManager.completed_indices.add(memory.media_download_url)
        StatsManager.successful_downloads_count += 1
        self._log_processed_indices(StatsManager.completed_indices)


    def _prune_memory_item(self, memory: Memory, file_path: Path) -> None:
        file_size_mb = self._convert_file_size(file_path)
        MemoriesRepository().prune_by_media_download_url(memory.media_download_url)
        log(f"Downloaded item {memory.filename_with_ext}. File size: {file_size_mb:.2f} MB. Successfully pruned from json.", "info")


    @staticmethod
    def _convert_file_size(file_path: Path) -> float:
        return file_path.stat().st_size / (1024 * 1024)


    @staticmethod
    def _log_processed_indices(indices: set[int]) -> None:
        if indices and len(indices) % 10 == 0:
            log(f"Successfully processed {len(indices)} items so far", "debug")
