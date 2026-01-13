import logging
from pathlib import Path
from datetime import datetime
from src.logger import JSONFormatter
from src.config import Config


class LogInitializer:
    def configure_logger(self, config):
        logger = logging.getLogger()
        logger.setLevel(config.from_args().cli_options["log_level"])

        log_path = self._build_log_path(config)
        self._ensure_log_dir(log_path)
        logger.addHandler(self._create_file_handler(log_path, config))


    def _build_log_path(self, config: Config) -> Path:
        return Path(config.logs_folder) / self._create_log_filename()


    @staticmethod
    def _ensure_log_dir(log_path: Path) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)


    def _create_log_filename(self) -> str:
        return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"


    def _create_file_handler(self, path: Path, config: Config) -> logging.Handler:
        handler = logging.FileHandler(path, encoding="utf-8", delay=True)
        handler.setLevel(config.from_args().cli_options["log_level"])
        handler.setFormatter(JSONFormatter())
        return handler
