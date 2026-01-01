import logging
from typing import Literal


def log(message: str, level: Literal["debug", "info", "warning", "error", "critical"]) -> None:
    logger = logging.getLogger("snapchat_extractor")
    getattr(logger, level)(message)
