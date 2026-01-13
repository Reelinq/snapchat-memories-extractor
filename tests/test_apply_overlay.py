import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import logging
from src.config import Config
from src.downloader.download_service import DownloadService

@pytest.mark.parametrize("apply_overlay", [True, False])
def test_apply_overlay_flag_behavior(apply_overlay):
    cli_options = {
        'max_concurrent_downloads': 2,
        'apply_overlay': apply_overlay,
        'write_metadata': True,
        'max_attempts': 1,
        'strict_location': False,
        'jpeg_quality': 95,
        'convert_to_jxl': True,
        'log_level': logging.CRITICAL,
        'request_timeout': 30,
        'ffmpeg_timeout': 60,
        'stream_chunk_size': 1024 * 1024
    }
    config = Config(cli_options=cli_options)
    ds = DownloadService(config, MagicMock())
    ds.content_processor = MagicMock()
    ds.content_processor.is_zip.return_value = True
    ds.content_processor.extract_media_from_zip.return_value = (b'data', '.jpg', b'overlay')
    ds.overlay_service = MagicMock()
    ds.metadata_service = MagicMock()
    memory = MagicMock()
    memory.media_type = "Image"
    memory.filename = "file"
    memory.filename_with_ext = "file.jpg"
    with patch("src.services.download_service.get_media_processor") as mock_proc:
        ds._process_zip(b'data', memory)
        if apply_overlay:
            assert mock_proc.return_value.apply_overlay.called
        else:
            assert not mock_proc.return_value.apply_overlay.called
