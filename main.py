from config import Config
from downloader import MemoryDownloader
from logger import init_logging
import sys

if __name__ == "__main__":
    config = Config.from_args()
    logger = init_logging(config)
    
    logger.info("Application started")
    
    downloader = MemoryDownloader(config)
    exit_code = 0
    exit_reason = "normal"
    
    try:
        downloader.run()
        logger.info("Download process completed successfully")
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user (Ctrl+C)")
        exit_code = 0
        exit_reason = "keyboard_interrupt"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        exit_code = 1
        exit_reason = "error"
    finally:
        try:
            downloader.close()
        except KeyboardInterrupt:
            # If user presses Ctrl+C during cleanup, exit immediately
            logger.warning("Cleanup interrupted by user")
            exit_code = 0
            exit_reason = "keyboard_interrupt_during_cleanup"
        
        # Wait briefly for any remaining background threads to finish logging
        import time
        time.sleep(0.1)
        
        logger.info(f"Application ended - reason: {exit_reason}, exit_code: {exit_code}")
        sys.exit(exit_code)
