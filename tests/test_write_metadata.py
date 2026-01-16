
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import logging
from src.config import Config
from src.memories import Memory
from src.media_dispatcher import process_media

@pytest.mark.parametrize("write_metadata", [True, False])
def test_write_metadata_flag_behavior(write_metadata, tmp_path):
    Config.cli_options = {
        'max_concurrent_downloads': 2,
        'apply_overlay': True,
        'write_metadata': write_metadata,
        'max_attempts': 1,
        'strict_location': False,
        'jpeg_quality': 95,
        'convert_to_jxl': True,
        'log_level': logging.CRITICAL,
        'request_timeout': 30,
        'ffmpeg_timeout': 60,
        'stream_chunk_size': 1024 * 1024,
        'cjxl_timeout': 10
    }
    memory = Memory.model_validate({
        "Date": "2023-12-05 12:34:56 UTC",
        "Media Download Url": "http://example.com/media.jpg",
        "Media Type": "Image",
        "Location": None
    })
    file_path = tmp_path / "file.jpg"
    file_path.write_bytes(b"data")
    with patch("src.metadata.image_metadata_writer.ImageMetadataWriter.write_image_metadata") as mock_write_metadata, patch("PIL.Image.open") as mock_img_open:
        mock_img_open.return_value.__enter__.return_value = MagicMock()
        process_media(memory, file_path)
        if write_metadata:
            assert mock_write_metadata.called
        else:
            assert not mock_write_metadata.called
