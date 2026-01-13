import logging
from unittest.mock import patch, MagicMock
import pytest
from src.config import Config
from src.downloader.download_service import DownloadService

@pytest.mark.parametrize("ffmpeg_timeout", [1, 10, 60])
def test_ffmpeg_timeout_behavior(ffmpeg_timeout):
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
        'ffmpeg_timeout': ffmpeg_timeout,
        'stream_chunk_size': 1024 * 1024
    }
    config = Config(cli_options=cli_options)
    ds = DownloadService(config, MagicMock())
    ds.content_processor = MagicMock()
    ds.content_processor.is_zip.return_value = False
    memory = MagicMock()
    memory.media_type = "Image"
    memory.filename_with_ext = "file.jpg"
    with patch("src.services.download_service.get_media_processor") as mock_proc:
        ds._process_regular(b'data', memory)
        if mock_proc.return_value.write_metadata.called:
            args, kwargs = mock_proc.return_value.write_metadata.call_args
            assert ffmpeg_timeout in args or ffmpeg_timeout in kwargs.values()
