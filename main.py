from src.config import Config
from src.downloader import MemoryDownloader
from src.logger import init_logging
from src.error_handling import handle_app_errors

if __name__ == "__main__":
    config = Config.from_args()
    logger = init_logging(config)
    logger.info("Application started")

    downloader = MemoryDownloader(config)

    @handle_app_errors(exit_code_on_error=1)
    def run_app(downloader):
        downloader.run()

    run_app(downloader)
