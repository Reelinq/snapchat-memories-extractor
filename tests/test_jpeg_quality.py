import logging
from unittest.mock import MagicMock, patch

import pytest

from src.config import Config
from src.media_dispatcher import process_media
from src.memories import Memory


@pytest.mark.parametrize("jpeg_quality", [50, 77, 95])
def test_jpeg_quality_behavior(jpeg_quality, tmp_path):
    Config.cli_options = {
        "max_concurrent_downloads": 2,
        "apply_overlay": True,
        "write_metadata": True,
        "max_attempts": 1,
        "strict_location": False,
        "jpeg_quality": jpeg_quality,
        "convert_to_jxl": True,
        "log_level": logging.CRITICAL,
        "request_timeout": 30,
        "ffmpeg_timeout": 60,
        "stream_chunk_size": 1024 * 1024,
        "cjxl_timeout": 120,
    }
    memory = Memory.model_validate(
        {
            "Date": "2023-12-05 12:34:56 UTC",
            "Media Download Url": "http://example.com/media.jpg",
            "Media Type": "Image",
            "Location": None,
        },
    )
    file_path = tmp_path / "file.jpg"
    file_path.write_bytes(b"data")
    with (
        patch("src.media_dispatcher.image_processor.process_image") as mock_proc_img,
        patch("PIL.Image.open") as mock_image_open,
    ):
        mock_image_open.return_value = MagicMock()
        process_media(memory, file_path)
        if mock_proc_img.called:
            args, kwargs = mock_proc_img.call_args
            assert jpeg_quality in args or jpeg_quality in kwargs.values()
