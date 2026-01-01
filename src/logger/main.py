import logging
import json
import inspect
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_caller_path():
    frame = inspect.currentframe()
    caller_path = frame.f_back.f_globals.get("__file__", None)
    del frame
    return caller_path


def log(message: str, level: str):
    logger = logging.getLogger(???)

    # Call the appropriate logger method based on level
    valid_levels = ["debug", "info", "warning", "error", "critical"]

    if level not in valid_levels:
        # log error
        return

    getattr(logger, level)(message)


class LazyFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=True):
        # delay=True means file is not opened until emit is called
        super().__init__(filename, mode, encoding, delay)
        self._file_created = False

    def emit(self, record):
        if not self._file_created:
            self._file_created = True
            Path(self.baseFilename).parent.mkdir(parents=True, exist_ok=True)
            if self.stream is None:
                # Open with line buffering (buffering=1)
                self.stream = open(self.baseFilename, self.mode,
                                   encoding=self.encoding, buffering=1)
        super().emit(record)
        self.flush()
        # Force OS-level flush
        if self.stream and not self.stream.closed:
            try:
                self.stream.flush()
                os.fsync(self.stream.fileno())
            except Exception:
                pass


def setup_logging(
    name: str = "snapchat_extractor",
    log_level: int = logging.INFO,
    log_dir: Optional[Path] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    logger.handlers.clear()

    if log_dir:
        json_log_path = Path(
            log_dir) / f"snapchat_extractor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        json_handler = LazyFileHandler(json_log_path, encoding="utf-8")
        json_handler.setLevel(logging.DEBUG)  # Pass everything through
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        logger.addHandler(json_handler)

    return logger


def get_logger(name: str = "snapchat_extractor") -> logging.Logger:
    return logging.getLogger(name)


def init_logging(config) -> logging.Logger:
    logger = setup_logging(
        name="snapchat_extractor",
        log_level=config.cli_options['log_level'],
        log_dir=config.logs_folder
    )
    logger.info("Snapchat Memories Extractor started")
    logger.debug(
        f"Configuration: concurrent={config.cli_options.get('max_concurrent_downloads')}, "
        f"overlay={config.cli_options.get('apply_overlay')}, metadata={config.cli_options.get('write_metadata')}"
    )
    return logger
