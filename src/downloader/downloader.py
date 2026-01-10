from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config.main import Config
from src.downloader.download_task import DownloadTask
from src.models import Memory
from src.memories_repository import MemoriesRepository
from src.logger.log import log
from src.ui.stats_manager import StatsManager
from src.ui.update_ui import UpdateUI


class MemoryDownloader:
    def run(self) -> None:
        completed_downloads_count = 0
        future_download_tasks = self._gather_future_download_tasks()

        if not future_download_tasks:
            log("No items to download.", "info")
            return

        for future in as_completed(future_download_tasks):
            index, _ = future_download_tasks[future]
            completed_downloads_count += 1

            file_path, download_succeeded = future.result()

            self._check_for_success(download_succeeded, index, file_path)


    def _gather_future_download_tasks(self):
        download_tasks = self._gather_download_tasks()
        max_workers = Config.from_args().cli_options['max_concurrent_downloads']
        executor = ThreadPoolExecutor(max_workers=max_workers)

        # Use dictonary becaude otherwsie index gets lost in 'as_completed'
        futures = {}

        for index, memory in enumerate(download_tasks):
            future = executor.submit(DownloadTask().run, memory)
            futures[future] = (index, memory)

        return futures


    @staticmethod
    def _gather_download_tasks():
        download_tasks = []
        raw_memory_items = MemoriesRepository().get_raw_items()

        for item in raw_memory_items:
            memory = Memory.model_validate(item)
            download_tasks.append(memory)

        return download_tasks


    def _check_for_success(self, download_succeeded: bool, index: int, file_path: Path) -> None:
        if download_succeeded:
            self._download_succeeded(index, file_path)
        else:
            StatsManager().failed_downloads_count += 1
        UpdateUI().run()


    def _download_succeeded(self, index: int, file_path: Path) -> None:
        self._prune_memory_item(index, file_path)
        StatsManager().completed_indices.add(index)
        StatsManager().successful_downloads_count += 1
        self._log_processed_indices(StatsManager().completed_indices)


    def _prune_memory_item(self, index: int, file_path: Path) -> None:
        file_size_mb = self._convert_file_size(file_path)
        MemoriesRepository().prune(index)
        log(f"Downloaded item {file_path.name}. File size: {file_size_mb:.2f} MB. Successfully pruned from json.", "info")


    @staticmethod
    def _convert_file_size(file_path: Path) -> float:
        if not file_path.exists():
            log(f"File not found: {file_path}", "error")
            return 0.0
        return file_path.stat().st_size / (1024 * 1024)


    @staticmethod
    def _log_processed_indices(indices: set[int]) -> None:
        if indices and len(indices) % 10 == 0:
            log(f"Successfully processed {len(indices)} items so far", "debug")
