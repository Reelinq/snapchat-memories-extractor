from src.config.main import Config
from src.downloader import MemoryDownloader
from src.logger.log_initializer import LogInitializer
from src.logger.log import log

if __name__ == "__main__":
    config = Config.from_args()

    logger = LogInitializer(config)
    log("Application started", "info")

    downloader = MemoryDownloader(config)

    def run_app(downloader):
        downloader.run()

    run_app(downloader)
