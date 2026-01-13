from src.downloader import SetupDownloader
from src.logger import LogInitializer, log
from src.ui import StatsManager, UpdateUI, Display
from src.config import Config


if __name__ == "__main__":
    LogInitializer().configure_logger(Config)
    StatsManager()

    log("Application started", "info")

    SetupDownloader().run(Config)

# ------------------------------------------------

    UpdateUI()._clear_display()
    Display().print_display(Config, finished = True)
    log("Application finished", "info")
