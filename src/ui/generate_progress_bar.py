class GenerateProgressBar:
    def __init__(self, current: int, total: int, bar_length=55) -> None:
        self.current = current
        self.total = total
        self.bar_length = bar_length

    def run(self) -> str:
        filled_bar_length = self._calculate_progress()
        return "█" * filled_bar_length + "░" * (
            self.bar_length - filled_bar_length
        )

    def _calculate_progress(self) -> int:
        if self.total == 0:
            return 0
        return int(self.bar_length * self.current / self.total)
