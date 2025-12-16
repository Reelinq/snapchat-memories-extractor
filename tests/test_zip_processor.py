import zipfile
from io import BytesIO
import pytest
from src.processors.zip_processor import ZipProcessor

@pytest.fixture
def zip_with_jpg_and_overlay():
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('test.jpg', b'jpgdata')
        zf.writestr('overlay.png', b'pngdata')
    return buf.getvalue()

@pytest.fixture
def zip_with_mp4_and_overlay():
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('video.mp4', b'mp4data')
        zf.writestr('overlay.png', b'pngdata2')
    return buf.getvalue()

@pytest.mark.parametrize("content,content_type,expected", [
    (b'PK\x03\x04dummyzipcontent', 'application/zip', True),
    (b'PK\x03\x04dummyzipcontent', 'something/zip', True),
    (b'PK\x03\x04dummyzipcontent', 'other', True),  # magic bytes
    (b'notazip', 'text/plain', False),
])
def test_is_zip(content, content_type, expected):
    assert ZipProcessor.is_zip(content, content_type) == expected

def test_extract_media_from_zip_jpg(zip_with_jpg_and_overlay):
    media, ext, overlay = ZipProcessor.extract_media_from_zip(
        zip_with_jpg_and_overlay)
    assert media == b'jpgdata'
    assert ext == '.jpg'
    assert overlay == b'pngdata'

def test_extract_media_from_zip_mp4(zip_with_mp4_and_overlay):
    media, ext, overlay = ZipProcessor.extract_media_from_zip(
        zip_with_mp4_and_overlay)
    assert media == b'mp4data'
    assert ext == '.mp4'
    assert overlay == b'pngdata2'
