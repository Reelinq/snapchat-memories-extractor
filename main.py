from config import Config
from downloader import MemoryDownloader
from logger import init_logging

if __name__ == "__main__":
    config = Config.from_args()
    logger = init_logging(config)

    try:
        downloader = MemoryDownloader(config)
        downloader.run()
        logger.info("Download process completed successfully")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
