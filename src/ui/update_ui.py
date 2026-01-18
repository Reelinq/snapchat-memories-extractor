import sys

from src.ui import Display


class UpdateUI:
    def run(self, state=None):
        self.clear_display()
        Display().print_display(state)

    @staticmethod
    def clear_display(lines=8):
        for _ in range(lines):
            sys.stdout.write("\033[F\033[K")
