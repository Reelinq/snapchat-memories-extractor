from src.downloader.setup_downloader import SetupDownloader
from src.downloader.downloader import MemoryDownloader
from src.logger.log_initializer import LogInitializer
from src.logger.log import log
from src.ui.stats_manager import StatsManager

if __name__ == "__main__":
    LogInitializer().configure_logger()
    StatsManager()
    log("Application started", "info")

    SetupDownloader().run()
    MemoryDownloader().run()
