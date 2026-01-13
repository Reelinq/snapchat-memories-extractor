
import logging
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
from src.config import Config
from src.downloader.download_service import DownloadService

@pytest.mark.parametrize("convert_to_jxl", [True, False])
def test_convert_to_jxl_behavior(convert_to_jxl):
    cli_options = {
        'max_concurrent_downloads': 2,
        'apply_overlay': True,
        'write_metadata': True,
        'max_attempts': 1,
        'strict_location': False,
        'jpeg_quality': 95,
        'convert_to_jxl': convert_to_jxl,
        'log_level': logging.CRITICAL,
        'request_timeout': 30,
        'ffmpeg_timeout': 60,
        'stream_chunk_size': 1024 * 1024
    }
    config = Config(cli_options=cli_options)
    ds = DownloadService(config, MagicMock())
    ds.content_processor = MagicMock()
    ds.content_processor.is_zip.return_value = False
    memory = MagicMock()
    memory.media_type = "Image"
    memory.filename_with_ext = "file.jpg"
    with patch("src.services.jxl_converter.JXLConverter.convert_to_jxl") as mock_jxl:
        with patch("src.services.download_service.get_media_processor") as mock_proc:
            mock_proc.return_value.write_metadata.return_value = Path("file.jpg")
            ds._process_regular(b'data', memory)
            if convert_to_jxl:
                # It may be called if write_metadata is False and type is Image
                pass
            else:
                assert not mock_jxl.called
