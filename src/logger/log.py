import logging
from typing import Literal


def log(message: str, level: Literal["debug", "info", "warning", "error", "critical"]) -> None:
    logger = logging.getLogger("__name__")
    getattr(logger, level)(message)
