import pytest
import tempfile
import shutil
from pathlib import Path
from src.config import Config

@pytest.mark.parametrize("cli_args, expected", [
    (["--stream-chunk-size", "2048"], {"stream_chunk_size": 2048 * 1024}),
    (["-S", "4096"], {"stream_chunk_size": 4096 * 1024}),
    (["--ffmpeg-timeout", "120"], {"ffmpeg_timeout": 120}),
    (["-f", "180"], {"ffmpeg_timeout": 180}),
    (["--request-timeout", "99"], {"request_timeout": 99}),
    (["-t", "77"], {"request_timeout": 77}),
    (["--concurrent", "9"], {"max_concurrent_downloads": 9}),
    (["-c", "2"], {"max_concurrent_downloads": 2}),
    (["--no-overlay"], {"apply_overlay": False}),
    (["-O"], {"apply_overlay": False}),
    (["--no-metadata"], {"write_metadata": False}),
    (["-M"], {"write_metadata": False}),
    (["--attempts", "7"], {"max_attempts": 7}),
    (["-a", "8"], {"max_attempts": 8}),
    (["--strict"], {"strict_location": True}),
    (["-s"], {"strict_location": True}),
    (["--jpeg-quality", "88"], {"jpeg_quality": 88}),
    (["-q", "77"], {"jpeg_quality": 77}),
    (["--no-jxl"], {"convert_to_jxl": False}),
    (["-J"], {"convert_to_jxl": False}),
    (["--log-level", "3"], {"log_level": 30}),
    (["-l", "DEBUG"], {"log_level": 10}),
])
def test_config_cli_flags(monkeypatch, cli_args, expected):
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Patch sys.argv for argparse
        import sys
        monkeypatch.setattr(sys, "argv", ["main.py"] + cli_args)
        config = Config.from_args()
        for key, value in expected.items():
            assert config.cli_options[key] == value, f"{key} expected {value}, got {config.cli_options[key]}"
    finally:
        shutil.rmtree(temp_dir)
