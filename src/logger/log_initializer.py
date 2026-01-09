import logging
from pathlib import Path
from datetime import datetime
from src.logger.formatter import JSONFormatter


class LogInitializer:
    def configure_logger(self) -> logging.Logger:
        logger = logging.getLogger("__name__")
        logger.setLevel(self.config.cli_options["log_level"])

        log_path = self._build_log_path()
        self._ensure_log_dir(log_path)
        logger.addHandler(self._create_file_handler(log_path))
        return logger

    def _build_log_path(self) -> Path:
        return Path(self.config.logs_folder) / self._create_log_filename()

    @staticmethod
    def _ensure_log_dir(log_path: Path) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def _create_log_filename(self) -> str:
        return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

    def _create_file_handler(self, path: Path) -> logging.Handler:
        handler = logging.FileHandler(path, encoding="utf-8", delay=True)
        handler.setLevel(self.config.cli_options["log_level"])
        handler.setFormatter(JSONFormatter())
        return handler
