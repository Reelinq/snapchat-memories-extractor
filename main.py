from src.config.main import Config
from src.downloader import MemoryDownloader
from src.logger.log_initializer import LogInitializer
from src.logger.log import log
from src.error_handling import handle_app_errors

if __name__ == "__main__":
    config = Config.from_args()

    logger = LogInitializer(config)
    log("Application started", "info")

    downloader = MemoryDownloader(config)

    @handle_app_errors(exit_code_on_error=1)
    def run_app(downloader):
        downloader.run()

    run_app(downloader)
