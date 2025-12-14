import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.config import Config
from src.downloader import MemoryDownloader
from src.models import Memory


class TestMemoryDownloaderStrict(unittest.TestCase):
    def test_strict_location_blocks_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                json_path=Path(tmpdir) / "memories_history.json",
                downloads_folder=Path(tmpdir) / "downloads",
                logs_folder=Path(tmpdir) / "logs",
                strict_location=True
            )
            downloader = MemoryDownloader(config)
            downloader.download_service = MagicMock()

            memory = Memory.model_validate({
                "Date": "2023-12-05 12:34:56 UTC",
                "Media Download Url": "http://example.com/media.jpg",
                "Media Type": "Image",
                "Location": None
            })

            success = downloader._download_task(0, memory)

            self.assertFalse(success)
            downloader.download_service.download_and_process.assert_not_called()
            self.assertTrue(downloader.errors)
            self.assertEqual(downloader.errors[-1]['code'], 'LOC')


if __name__ == "__main__":
    unittest.main()
