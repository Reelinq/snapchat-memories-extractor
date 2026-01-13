from pathlib import Path
from src.config import Config
from src.memories import Memory
from src.logger import log
from src.downloader import DownloadService


class DownloadTask:
    def run(self, memory: Memory, config: Config) -> tuple[Path, bool]:
        if not self._ensure_strict_location(memory, config):
            return None, False

        return DownloadService().run(memory, config)


    def _ensure_strict_location(self, memory: Memory, config: Config) -> bool:
        if config.from_args().cli_options['strict_location'] and memory.location_coords is None:
            log(f"Skipping {memory.filename_with_ext}: No location data available", "warning")
            return False

        return True
