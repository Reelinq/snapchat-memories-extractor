import sys
from src.ui import Display


class UpdateUI():
    def run(self, config):
        self._clear_display()
        Display(config).print_display()


    @staticmethod
    def _clear_display(lines = 8):
        for _ in range(lines):
            sys.stdout.write('\033[F\033[K')
