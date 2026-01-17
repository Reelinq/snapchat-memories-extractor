import zipfile
from io import BytesIO
import pytest
from src.zip_processor import ZipProcessor


import zipfile
import tempfile
import pytest
from pathlib import Path
from src.zip_processor import ZipProcessor
from src.config import Config

@pytest.fixture
from pathlib import Path

from typing import Callable

@pytest.fixture
def make_zip(tmp_path: Path) -> Callable:
    def _make_zip(media_name: str, media_data: bytes, overlay_name: str = None, overlay_data: bytes = None) -> Path:
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(media_name, media_data)
            if overlay_name and overlay_data:
                zf.writestr(overlay_name, overlay_data)
        return zip_path
    return _make_zip

def test_extract_media_from_zip_jpg(make_zip: Callable) -> None:
    Config.cli_options = {"apply_overlay": True}
    zip_path = make_zip("test.jpg", b"jpgdata", "overlay.png", b"pngdata")
    zp = ZipProcessor(str(zip_path))
    media, overlay, ext = zp.extract_media_from_zip()
    assert media == b"jpgdata"
    assert ext == ".jpg"
    assert overlay == b"pngdata"

def test_extract_media_from_zip_mp4(make_zip: Callable) -> None:
    Config.cli_options = {"apply_overlay": True}
    zip_path = make_zip("video.mp4", b"mp4data", "overlay.png", b"pngdata2")
    zp = ZipProcessor(str(zip_path))
    media, overlay, ext = zp.extract_media_from_zip()
    assert media == b"mp4data"
    assert ext == ".mp4"
    assert overlay == b"pngdata2"

def test_extract_media_from_zip_no_overlay(make_zip: Callable) -> None:
    Config.cli_options = {"apply_overlay": False}
    zip_path = make_zip("test.jpg", b"jpgdata", "overlay.png", b"pngdata")
    zp = ZipProcessor(str(zip_path))
    media, overlay, ext = zp.extract_media_from_zip()
    assert media == b"jpgdata"
    assert ext == ".jpg"
    assert overlay is None
