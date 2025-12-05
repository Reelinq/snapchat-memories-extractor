import unittest
from services.metadata_service import *


from unittest.mock import patch, MagicMock
from pathlib import Path

class TestMetadataService(unittest.TestCase):
    @patch("services.metadata_service.Image.open")
    @patch("services.metadata_service.piexif.dump", return_value=b"exifbytes")
    def test_write_image_metadata(self, mock_dump, mock_open):
        memory = MagicMock()
        memory.exif_datetime = "2023:12:05 12:34:56"
        memory.location_coords = (37.0, -122.0)
        service = MetadataService()
        mock_img = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_img
        service._write_image_metadata(memory, Path("dummy.jpg"))
        self.assertTrue(mock_img.save.called)
        self.assertTrue(mock_dump.called)

    @patch.object(Path, "replace", return_value=None)
    @patch("services.metadata_service.subprocess.run")
    @patch("services.metadata_service.imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg")
    def test_write_video_metadata(self, mock_ffmpeg, mock_run, mock_replace):
        memory = MagicMock()
        memory.video_creation_time = "2023-12-05T12:34:56"
        memory.location_coords = (37.0, -122.0)
        service = MetadataService()
        mock_run.return_value.returncode = 0
        service._write_video_metadata(memory, Path("dummy.mp4"), 10)
        self.assertTrue(mock_run.called)

if __name__ == "__main__":
    unittest.main()
