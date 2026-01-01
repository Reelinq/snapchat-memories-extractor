import logging
import inspect
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.logger.formatter import JSONFormatter


def get_caller_path():
    frame = inspect.currentframe()
    caller_path = frame.f_back.f_globals.get("__file__", None)
    del frame
    return caller_path


def log(message: str, level: str):
    logger = logging.getLogger(__name__)
    valid_levels = ["debug", "info", "warning", "error", "critical"]

    if level not in valid_levels:
        # log error
        return

    getattr(logger, level)(message)


def create_log_filename() -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"snapchat_extractor_{timestamp}.jsonl"


def init_logging(config) -> logging.Logger:
    logger = logging.getLogger("snapchat_extractor")
    logger.setLevel(config.cli_options['log_level'])

    json_log_path = Path(config.logs_folder) / create_log_filename()

    json_handler = logging.FileHandler(
        json_log_path, encoding="utf-8", delay=True)
    json_handler.setFormatter(JSONFormatter())
    logger.addHandler(json_handler)

    return logger
