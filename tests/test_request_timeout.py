import logging
from unittest.mock import MagicMock, patch

import pytest

from src.config import Config
from src.downloader.download_service import DownloadService
from src.memories import Memory


@pytest.mark.parametrize("timeout", [5, 30, 99])
def test_request_timeout_behavior(timeout: int, tmp_path) -> None:
    Config.cli_options = {
        "max_concurrent_downloads": 2,
        "apply_overlay": True,
        "write_metadata": True,
        "max_attempts": 1,
        "strict_location": False,
        "jpeg_quality": 95,
        "convert_to_jxl": True,
        "log_level": logging.CRITICAL,
        "request_timeout": timeout,
        "ffmpeg_timeout": 60,
        "stream_chunk_size": 1024 * 1024,
    }
    memory = Memory.model_validate(
        {
            "Date": "2023-12-05 12:34:56 UTC",
            "Media Download Url": "http://example.com/file.jpg",
            "Media Type": "Image",
            "Location": None,
        },
    )
    with (
        patch("requests.Session.get") as mock_get,
        patch("PIL.Image.open") as mock_img_open,
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_response.content = b"data"
        mock_get.return_value = mock_response
        mock_img_open.return_value.__enter__.return_value = MagicMock()
        ds = DownloadService(memory)
        ds._build_session = MagicMock(return_value=MagicMock(get=mock_get))
        ds._store_downloaded_memory = MagicMock(return_value=tmp_path / "file.jpg")
        ds.memory = memory
        ds.run()
        mock_get.assert_called_with(memory.media_download_url, timeout=timeout)
