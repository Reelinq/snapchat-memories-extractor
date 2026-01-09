from src.downloader.setup_downloader import SetupDownloader
from src.downloader.downloader import MemoryDownloader
from src.logger.log_initializer import LogInitializer
from src.logger.log import log

if __name__ == "__main__":
    logger = LogInitializer().configure_logger()
    log("Application started", "info")

    SetupDownloader().run()
    MemoryDownloader().run()
