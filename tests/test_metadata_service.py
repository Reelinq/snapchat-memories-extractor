from pathlib import Path
from unittest.mock import MagicMock
import pytest
from src.metadata.metadata_dispatcher import MetadataService

@pytest.fixture
def metadata_service():
    return MetadataService()

@pytest.fixture
def mock_memory_image():
    memory = MagicMock()
    memory.exif_datetime = "2023:12:05 12:34:56"
    memory.location_coords = (37.0, -122.0)
    return memory

@pytest.fixture
def mock_memory_video():
    memory = MagicMock()
    memory.video_creation_time = "2023-12-05T12:34:56"
    memory.location_coords = (37.0, -122.0)
    return memory

def test_write_image_metadata(metadata_service, mock_memory_image, mocker):
    mock_img = MagicMock()
    mock_open = mocker.patch("src.services.metadata_service.Image.open")
    mock_open.return_value.__enter__.return_value = mock_img

    mock_dump = mocker.patch(
        "src.services.metadata_service.piexif.dump", return_value=b"exifbytes")

    metadata_service._write_image_metadata(mock_memory_image, Path("dummy.jpg"))

    assert mock_img.save.called
    assert mock_dump.called


def test_write_video_metadata(metadata_service, mock_memory_video, mocker):
    mock_replace = mocker.patch.object(Path, "replace", return_value=None)
    mock_run = mocker.patch("src.services.metadata_service.subprocess.run")
    mock_run.return_value.returncode = 0

    mock_ffmpeg = mocker.patch(
        "src.services.metadata_service.imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg")

    metadata_service._write_video_metadata(
        mock_memory_video, Path("dummy.mp4"), 10)

    assert mock_run.called
