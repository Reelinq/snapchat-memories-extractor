from src.downloader.setup_downloader import SetupDownloader
from src.logger.log_initializer import LogInitializer
from src.logger.log import log
from src.ui.stats_manager import StatsManager
from src.ui.display import Display
from src.ui.update_ui import UpdateUI


if __name__ == "__main__":
    LogInitializer().configure_logger()
    StatsManager()

    log("Application started", "info")

    SetupDownloader().run()

# ------------------------------------------------

    UpdateUI()._clear_display()
    Display().print_display(finished = True)
    log("Application finished", "info")
