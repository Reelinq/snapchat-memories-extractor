import logging
from unittest.mock import patch

import pytest

from src.config import Config
from src.downloader.downloader import MemoryDownloader


@pytest.mark.parametrize("max_workers", [1, 3, 5])
def test_max_concurrent_downloads_sets_threadpool(max_workers: int) -> None:
    cli_options = {
        "max_concurrent_downloads": max_workers,
        "apply_overlay": True,
        "write_metadata": True,
        "max_attempts": 1,
        "strict_location": False,
        "jpeg_quality": 95,
        "convert_to_jxl": True,
        "log_level": logging.CRITICAL,
        "request_timeout": 30,
        "ffmpeg_timeout": 60,
        "stream_chunk_size": 1024 * 1024,
    }
    Config.cli_options = cli_options
    with patch(
        "src.downloader.downloader.ThreadPoolExecutor.__init__", return_value=None,
    ) as mock_exec:
        md = MemoryDownloader()
        md._gather_download_tasks = lambda: []  # Prevent actual download logic
        md.run()
        mock_exec.assert_called_with(max_workers=max_workers)
