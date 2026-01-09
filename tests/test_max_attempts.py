import logging
from unittest.mock import MagicMock
import pytest
from src.config import Config
from src.downloader.downloader import MemoryDownloader

@pytest.mark.parametrize("max_attempts", [1, 2, 3])
def test_max_attempts_behavior(max_attempts):
    cli_options = {
        'max_concurrent_downloads': 2,
        'apply_overlay': True,
        'write_metadata': True,
        'max_attempts': max_attempts,
        'strict_location': False,
        'jpeg_quality': 95,
        'convert_to_jxl': True,
        'log_level': logging.CRITICAL,
        'request_timeout': 30,
        'ffmpeg_timeout': 60,
        'stream_chunk_size': 1024 * 1024
    }
    config = Config(cli_options=cli_options)
    md = MemoryDownloader(config)
    md.ui_stuff = MagicMock()
    md.failed_downloads_count = 1
    md.ui_stuff.side_effect = lambda: setattr(md, 'failed_downloads_count', 0)
    md.run()
    assert md.ui_stuff.call_count <= max_attempts
