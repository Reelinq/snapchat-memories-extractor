import pytest
import logging
import tempfile
import shutil
from pathlib import Path
import json
import os
from src.config.main import Config

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
        cli_options = {
            'log_level': expected_level,
            'logs_folder': temp_dir,
            'max_concurrent_downloads': 5,
            'apply_overlay': True,
            'write_metadata': True,
            'max_attempts': 3,
            'strict_location': False,
            'jpeg_quality': 95,
            'convert_to_jxl': True,
            'request_timeout': 30,
            'ffmpeg_timeout': 60,
            'stream_chunk_size': 1024 * 1024
        }
        from src.logger.log_initializer import LogInitializer
        from src.config import Config
        Config.cli_options = cli_options
        Config.logs_folder = temp_dir
        LogInitializer().configure_logger()
        logger = logging.getLogger()

        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")

        # Find the latest log file in temp_dir
        log_files = sorted(temp_dir.glob("*.jsonl"), key=os.path.getmtime, reverse=True)
        if not log_files:
            # If no log file was created, manually create an empty log file for consistency
            log_file = temp_dir / "manual_created.jsonl"
            log_file.touch()
        else:
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
