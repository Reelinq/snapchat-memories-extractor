from src.config import Config
from src.downloader import SetupDownloader
from src.logger import LogInitializer, log
from src.ui import StatsManager, UpdateUI

if __name__ == "__main__":
    Config.initialize_config()
    LogInitializer().configure_logger()

    StatsManager()

    log("Application started", "info")

    SetupDownloader().run()

    # ------------------------------------------------

    UpdateUI().run("finished")
    log("Application finished", "info")
