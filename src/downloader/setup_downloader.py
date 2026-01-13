from src.config import Config
from src.downloader import MemoryDownloader
from src.ui import Display, StatsManager
from src.logger import log


class SetupDownloader:
    def run(self) -> None:
        max_attempts = Config.from_args().cli_options['max_attempts']

        for attempt in range(max_attempts):
            Display().print_display(loading=True)
            log(f"Starting attempt {attempt + 1} / {max_attempts}...", "info")
            StatsManager.new_attempt()
            MemoryDownloader().run()

            if not self._check_for_failures():
                break

        if StatsManager.failed_downloads_count > 0:
            log(f"Max attempts ({max_attempts}) reached with failures", "info")


    @staticmethod
    def _check_for_failures() -> bool:
        if StatsManager.failed_downloads_count == 0:
            log("All downloads successful, no retry needed", "info")
            return False
        return True
