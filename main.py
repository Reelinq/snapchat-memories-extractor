from config import Config
from downloader import MemoryDownloader
from logger import init_logging
import sys

if __name__ == "__main__":
    config = Config.from_args()
    logger = init_logging(config)

    downloader = MemoryDownloader(config)
    try:
        downloader.run()
        logger.info("Download process completed successfully")
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        try:
            downloader.close()
        except KeyboardInterrupt:
            # If user presses Ctrl+C during cleanup, exit immediately
            sys.exit(0)
