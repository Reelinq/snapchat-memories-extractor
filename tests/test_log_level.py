import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from src.config import Config
from src.logger import init_logging
import json
import os

@pytest.mark.parametrize("level_input,expected_level,expected_levels", [
    ('0', logging.CRITICAL + 10, []),
    ('1', logging.CRITICAL, ["CRITICAL"]),
    ('2', logging.ERROR, ["ERROR", "CRITICAL"]),
    ('3', logging.WARNING, ["WARNING", "ERROR", "CRITICAL"]),
    ('4', logging.INFO, ["INFO", "WARNING", "ERROR", "CRITICAL"]),
    ('5', logging.DEBUG, ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
])
def test_log_file_levels(level_input, expected_level, expected_levels):
    temp_dir = Path(tempfile.mkdtemp())
    try:
        config = Config(log_level=expected_level, logs_folder=temp_dir)
        logger = init_logging(config)

        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")

        # Find the latest log file in temp_dir
        log_files = sorted(temp_dir.glob("*.jsonl"), key=os.path.getmtime, reverse=True)
        assert log_files, "No log file created"
        log_file = log_files[0]

        # Read log file and collect levels
        with open(log_file, "r", encoding="utf-8") as f:
            log_lines = [json.loads(line) for line in f if line.strip()]

        found_levels = [entry["level"] for entry in log_lines if entry["message"].endswith("message")]

        # Check that only expected levels are present
        assert set(found_levels) == set(expected_levels), f"Expected {expected_levels}, found {found_levels}"

    finally:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        shutil.rmtree(temp_dir)
