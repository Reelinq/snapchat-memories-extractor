from pathlib import Path

from src.config import Config
from src.downloader.download_service import DownloadService
from src.logger import log
from src.memories import Memory


class DownloadTask:
    def __init__(self, memory: Memory) -> None:
        self.memory = memory

    def run(self) -> tuple[Path, bool]:
        if not self._ensure_strict_location():
            return None, False

        return DownloadService(self.memory).run()

    def _ensure_strict_location(self) -> bool:
        if (
            Config.cli_options["strict_location"]
            and self.memory.location_coords is None
        ):
            log(
                f"Skipping {self.memory.filename_with_ext}: No location data available",
                "warning",
            )
            return False

        return True
