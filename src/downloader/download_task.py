from src.config.main import Config
from src.models import Memory
from src.logger.log import log
from src.services.download_service import DownloadService


class DownloadTask:
    def __init__(self, memory: Memory) -> bool:
        if not self._ensure_strict_location(memory):
            return False

        file_path, download_succeeded = DownloadService().run(memory)
        self._update_stats_from_download()

        return file_path, download_succeeded


    def _update_stats_from_download(self):
        pass
        #TODO: Add stats update logic
        """if self.download_service.errors:
            self.stats.errors.extend(self.download_service.errors)
            self.download_service.errors.clear()
        self.stats.total_bytes += self.download_service.total_bytes
        self.download_service.total_bytes = 0"""


    def _ensure_strict_location(self, memory: Memory) -> bool:
        if Config.cli_options['strict_location'] and memory.location_coords is None:
            log(f"Skipping {memory.filename_with_ext}: No location data available", "warning")
            return False

        return True
