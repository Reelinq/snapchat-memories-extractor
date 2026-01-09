import logging
from unittest.mock import patch, MagicMock
import pytest
from src.config import Config
from src.download_service import DownloadService

@pytest.mark.parametrize("chunk_size", [512, 2048, 4096])
def test_stream_chunk_size_behavior(chunk_size):
    cli_options = {
        'max_concurrent_downloads': 2,
        'apply_overlay': True,
        'write_metadata': True,
        'max_attempts': 1,
        'strict_location': False,
        'jpeg_quality': 95,
        'convert_to_jxl': True,
        'log_level': logging.CRITICAL,
        'request_timeout': 30,
        'ffmpeg_timeout': 60,
        'stream_chunk_size': chunk_size
    }
    config = Config(cli_options=cli_options)
    ds = DownloadService(config, MagicMock())
    memory = MagicMock()
    memory.media_download_url = "http://example.com/file.jpg"
    ds.session = MagicMock()
    ds.session.get.return_value = MagicMock()
    ds.session.get.return_value.iter_content.return_value = [b'data']
    ds.session.get.return_value.headers = {"Content-Type": "image/jpeg"}
    ds.session.get.return_value.raise_for_status = lambda: None
    ds.content_processor = MagicMock()
    ds.content_processor.is_zip.return_value = False
    # Patch iter_content to check chunk_size
    def iter_content(chunk_size_arg):
        assert chunk_size_arg == chunk_size
        return [b'data']
    ds.session.get.return_value.iter_content = iter_content
    ds.download_and_process(memory)
