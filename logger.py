import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra fields if provided
        if hasattr(record, "extra_data") and record.extra_data:
            log_obj.update(record.extra_data)

        return json.dumps(log_obj, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        if sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, self.RESET)
            level_str = f"{color}[{record.levelname}]{self.RESET}"
        else:
            level_str = f"[{record.levelname}]"

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        message = record.getMessage()

        log_line = f"{timestamp} {level_str} {message}"

        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"

        return log_line


class FlushingFileHandler(logging.FileHandler):
    # FileHandler that flushes after each log record for real-time logging.
    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logging(
    name: str = "snapchat_extractor",
    log_level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    enable_json: bool = True,
    enable_console: bool = True,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Logger captures everything

    logger.handlers.clear()

    # Console handler (human-readable) - only show INFO and above
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)  # Filter to INFO+ for clean console
        console_formatter = ConsoleFormatter()
        console_handler.setFormatter(console_formatter)
        # Flush console output immediately
        sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
        logger.addHandler(console_handler)

    # JSON file handler (structured logs) - capture DEBUG and above
    if enable_json and log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(exist_ok=True)

        json_log_path = log_dir / f"snapchat_extractor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        json_handler = FlushingFileHandler(json_log_path, encoding="utf-8")
        json_handler.setLevel(logging.DEBUG)  # Capture all levels for JSON logs
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        logger.addHandler(json_handler)

        logger.info(f"JSON logs being written to: {json_log_path}")

    return logger


def get_logger(name: str = "snapchat_extractor") -> logging.Logger:
    return logging.getLogger(name)


def init_logging(config) -> logging.Logger:
    logger = setup_logging(
        name="snapchat_extractor",
        log_level=config.log_level,
        log_dir=config.logs_folder,
        enable_json=True,
        enable_console=True,
    )
    logger.info("Snapchat Memories Extractor started")
    logger.debug(
        f"Configuration: concurrent={config.max_concurrent_downloads}, "
        f"overlay={config.apply_overlay}, metadata={config.write_metadata}"
    )
    return logger
