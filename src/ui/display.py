from time import time
from src.ui.stats_manager import StatsManager
from src.ui.generate_progress_bar import GenerateProgressBar
from src.ui.format_time import format_time

display_size = 70

class Display:
    def print_display(self):
        total = StatsManager().total_files
        current = StatsManager().successful_downloads_count + \
            StatsManager().failed_downloads_count
        remaining = total - current
        percent = (current / total * 100) if total > 0 else 0
        progress_bar = GenerateProgressBar().run(current, total)
        elapsed_time = int(time() - StatsManager().start_time)
        successful = StatsManager().successful_downloads_count
        failed = StatsManager().failed_downloads_count
        eta = self._calculate_eta(current, elapsed_time, remaining)

        line1 = ' SNAPCHAT MEMORIES DOWNLOADER '
        line2 = f"  [{progress_bar}] {percent:5.1f}%"
        line3 = f"  📥 Downloaded: {successful:>5}  │  ❌ Failed: {failed:>5}  │  ⏳ Remaining: {remaining:>5}"
        line4 = f"  ⏱️  Elapsed: {format_time(elapsed_time):>10}  │  🕐 ETA: {eta:>30}"

        print(f"╔{'═' * display_size}╗")
        print(f"║{self.padding_line(line1)}║")
        print(f"╠{'═' * display_size}╣")
        print(f"║{self.padding_line(line2)}║")
        print(f"╠{'═' * display_size}╣")
        print(f"║{self.padding_line(line3)}║")
        print(f"║{self.padding_line(line4)}║")
        print(f"╚{'═' * display_size}╝")


    @staticmethod
    def _calculate_eta(current: int, elapsed_time: int, remaining: int):
        if current == 0:
            return "calculating..."

        avg_time = elapsed_time / current
        eta = avg_time * remaining
        return format_time(eta)


    def padding_line(self, content, total_width=display_size):
        visible_width = self.display_width(content)
        padding_needed = total_width - visible_width
        return content + (' ' * max(0, padding_needed))


    def display_width(self, text: str) -> int:
        width = 0
        for character in text:
            codepoint = ord(character)
            width += 2 if self._is_codepoint_emoji(codepoint) else 1
        return width


    @staticmethod
    def _is_codepoint_emoji(codepoint: int) -> bool:
        if (
            0x1F300 <= codepoint <= 0x1F5FF or  # Misc Symbols and Pictographs
            0x1F600 <= codepoint <= 0x1F64F or  # Emoticons
            0x1F680 <= codepoint <= 0x1F6FF or  # Transport & Map Symbols
            0x2600 <= codepoint <= 0x26FF or    # Misc symbols
            0x2700 <= codepoint <= 0x27BF or    # Dingbats
            0x1F900 <= codepoint <= 0x1F9FF     # Supplemental Symbols and Pictographs
        ):
            return True
        return False
