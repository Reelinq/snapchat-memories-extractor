from pathlib import Path
from src.config import Config
from src.memories import Memory
from src.logger import log
from src.downloader.download_service import DownloadService


class DownloadTask:
    def __init__(self, memory: Memory, config: Config):
        self.memory = memory
        self.config = config


    def run(self) -> tuple[Path, bool]:
        if not self._ensure_strict_location():
            return None, False

        return DownloadService(self.config, self.memory).run()

    def _ensure_strict_location(self) -> bool:
        if self.config.from_args().cli_options['strict_location'] and self.memory.location_coords is None:
            log(f"Skipping {self.memory.filename_with_ext}: No location data available", "warning")
            return False

        return True
