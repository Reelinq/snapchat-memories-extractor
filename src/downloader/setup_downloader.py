from src.config import Config
from src.downloader.downloader import MemoryDownloader
from src.ui import Display, StatsManager
from src.logger import log


class SetupDownloader:
    def run(self, config: Config) -> None:
        max_attempts = config.from_args().cli_options['max_attempts']

        for attempt in range(max_attempts):
            Display(config).print_display(loading=True)
            log(f"Starting attempt {attempt + 1} / {max_attempts}...", "info")
            StatsManager.new_attempt()
            MemoryDownloader(config).run()

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
