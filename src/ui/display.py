from time import time

from src.config import Config
from src.ui.format_time import format_time
from src.ui.generate_progress_bar import GenerateProgressBar
from src.ui.stats_manager import StatsManager

display_size = 70


class Display:
    def __init__(self):
        total = StatsManager.total_files
        current = (
            StatsManager.successful_downloads_count
            + StatsManager.failed_downloads_count
        )
        self.remaining = total - current
        self.progress_bar = GenerateProgressBar(current, total).run()
        self.percent = (current / total * 100) if total > 0 else 0
        self.successful = StatsManager.successful_downloads_count
        self.failed = StatsManager.failed_downloads_count
        self.elapsed_time = int(time() - StatsManager.start_time)
        self.eta = self._calculate_eta(current, self.elapsed_time, self.remaining)

    def print_display(self, state):
        line1 = self._get_first_line()
        line2 = f"  [{self.progress_bar}] {self.percent:5.1f}%"

        if state == "loading":
            line3, line4 = self._get_loading_display_lines()
        elif state == "interrupted":
            line3, line4 = self._get_download_interruption_display_lines()
        elif state == "finished":
            line3, line4 = self._get_finished_display_lines()
        else:
            line3, line4 = self._get_base_display_lines()

        print(f"╔{'═' * display_size}╗")
        print(f"║{self._padding_line(line1)}║")
        print(f"╠{'═' * display_size}╣")
        print(f"║{self._padding_line(line2)}║")
        print(f"╠{'═' * display_size}╣")
        print(f"║{self._padding_line(line3)}║")
        print(f"║{self._padding_line(line4)}║")
        print(f"╚{'═' * display_size}╝")

    def _get_first_line(self) -> str:
        attempt = str(StatsManager.current_attempt)
        total_attempts = Config.cli_options["max_attempts"]
        left = " SNAPCHAT MEMORIES DOWNLOADER"
        right = f"ATTEMPT {attempt} / {total_attempts} "
        return left.ljust(display_size - len(right)) + right

    @staticmethod
    def _calculate_eta(current: int, elapsed_time: int, remaining: int):
        if current == 0:
            return "calculating..."

        avg_time = elapsed_time / current
        eta = avg_time * remaining
        return format_time(eta)

    @staticmethod
    def _get_loading_display_lines():
        line3 = "  ⏳ Initializing, scanning your memories..."
        line4 = "  📋 Preparing download list..."
        return line3, line4

    def _get_download_interruption_display_lines(self):
        line3 = "  ⚠️ Download interrupted by user."
        line4 = "  ⏳ Processing unfinished downloads, please wait..."
        return line3, line4

    def _get_finished_display_lines(self):
        line3 = "  ✅ Download process complete."
        line4 = f"  📥 Downloaded: {self.successful}  │  ❌ Failed: {self.failed}  │  🕐 Total Time: {format_time(self.elapsed_time):>10}"
        return line3, line4

    def _get_base_display_lines(self):
        line3 = f"  📥 Downloaded: {self.successful}  │  ❌ Failed: {self.failed}  │  📁 Remaining: {self.remaining}"
        line4 = f"  🕐  Elapsed: {format_time(self.elapsed_time):>10}  │  ⏳ ETA: {self.eta:>10}"
        return line3, line4

    def _padding_line(self, content, total_width=display_size):
        visible_width = self._display_width(content)
        padding_needed = total_width - visible_width
        return content + (" " * max(0, padding_needed))

    def _display_width(self, text: str) -> int:
        width = 0
        for character in text:
            width += 2 if self._has_double_width(character) else 1
        return width

    @staticmethod
    def _has_double_width(character: str) -> bool:
        if character in "📥❌📁🕐⏳📋⚠️✅":
            return True
        return False
