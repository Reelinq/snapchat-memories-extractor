import logging
from typing import Literal, Optional

def log(message: str, level: Literal["debug", "info", "warning", "error", "critical"], error_code: Optional[str] = None) -> None:
    logger = logging.getLogger()

    if level == "error" and error_code:
        extra = {'error_code': error_code}
        getattr(logger, level)(message, extra=extra, stacklevel=2)
    else:
        getattr(logger, level)(message, stacklevel=2)
