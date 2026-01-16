import logging
from unittest.mock import patch, MagicMock
import pytest
from src.config import Config
from src.memories import Memory
from src.media_dispatcher import process_media

@pytest.mark.parametrize("ffmpeg_timeout", [1, 10, 60])
def test_ffmpeg_timeout_behavior(ffmpeg_timeout, tmp_path):
    Config.cli_options = {
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
    memory = Memory.model_validate({
        "Date": "2023-12-05 12:34:56 UTC",
        "Media Download Url": "http://example.com/media.mp4",
        "Media Type": "Video",
        "Location": None
    })
    file_path = tmp_path / "file.mp4"
    file_path.write_bytes(b"data")
    with patch("src.media_dispatcher.video_processor.ProcessVideo.run") as mock_proc_vid:
        process_media(memory, file_path)
        assert mock_proc_vid.called
