from src.config.main import Config
from src.stats_manager import StatsManager
from src.logger.log import log


class SetupDownloader:
    def run(self) -> None:
        max_attempts = Config.from_args().cli_options['max_attempts']
        current_attempt_number = 0
        failure_count = StatsManager().failed_downloads_count

        while current_attempt_number < max_attempts or failure_count != 0:
            self._initialize_retry_attempt(current_attempt_number, max_attempts)
            self._ui_stuff()
            self._run()

            current_attempt_number += 1


    @staticmethod
    def _initialize_retry_attempt(attempt: int, max_attempts: int) -> None:
        if attempt > 0:
            log(f"Starting attempt {attempt + 1}/{max_attempts}...", "info")
            StatsManager().reset()


    @staticmethod
    def _ui_stuff():
        """clear_lines(10)
        total_time = time.time() - self.start_time
        print_status_threadsafe(self.total_files_count, self.total_files_count, self.stats.successful_downloads_count,
                                self.stats.failed_downloads_count, total_time, "✅ COMPLETE!")"""
