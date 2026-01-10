import sys
from src.ui.display import Display


class UpdateUI():
    def run(self):
        self._clear_display()
        Display().print_display()


    @staticmethod
    def _clear_display(lines = 8):
        for _ in range(lines):
            sys.stdout.write('\033[F\033[K')
