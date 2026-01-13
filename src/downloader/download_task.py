from pathlib import Path
from src.config.main import Config
from src.memories.memory_model import Memory
from src.logger.log import log
from src.downloader.download_service import DownloadService


class DownloadTask:
    def run(self, memory: Memory) -> tuple[Path, bool]:
        if not self._ensure_strict_location(memory):
            return None, False

        return DownloadService().run(memory)


    def _ensure_strict_location(self, memory: Memory) -> bool:
        if Config.from_args().cli_options['strict_location'] and memory.location_coords is None:
            log(f"Skipping {memory.filename_with_ext}: No location data available", "warning")
            return False

        return True
