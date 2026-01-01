import logging
from datetime import datetime
import json


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = self._get_base_log(record)

        if record.levelno != logging.INFO:
            log_obj.update(self.get_log_context(record))

        return json.dumps(log_obj)

    def _get_base_log(self, record: logging.LogRecord) -> dict:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

    def get_log_context(self, record: logging.LogRecord) -> dict:
        return {
            "file_path": record.pathname,
            "function": record.funcName,
            "line": record.lineno,
        }
