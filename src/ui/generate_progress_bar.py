class GenerateProgressBar:
    def run(self, current: int, total: int, bar_length = 55) -> str:
        filled_bar_length = self._calculate_progress(total, current, bar_length)
        progress_bar_display = (
            '█' * filled_bar_length +
            '░' * (bar_length - filled_bar_length)
        )
        return progress_bar_display


    @staticmethod
    def _calculate_progress(total: int, current: int, bar_length: int) -> int:
        if total == 0:
            return 0
        return int(bar_length * current / total)
