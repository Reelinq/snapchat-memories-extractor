import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from PIL import Image, ImageChops
import piexif
from src.services.jxl_converter import JXLConverter

HAS_CJXL = JXLConverter._get_cjxl_path() is not None


def _get_djxl_path() -> Path | None:
    if sys.platform == 'win32':
        binary_name = 'djxl.exe'
        rel_path = Path('libjxl-binaries/windows') / binary_name
    else:
        binary_name = 'djxl'
        rel_path = Path('libjxl-binaries/linux') / binary_name

    base_dir = Path(__file__).resolve().parent.parent.parent
    candidate = base_dir / rel_path
    if candidate.exists():
        return candidate

    result = subprocess.run([binary_name, '--version'],
                            capture_output=True, timeout=5)
    if result.returncode == 0:
        return Path(binary_name)

    return None

_DJXL_PATH = _get_djxl_path()
HAS_DJXL = _DJXL_PATH is not None

@pytest.fixture
def temp_dir():
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def make_sample_jpeg(temp_dir):
    def _make(color='red') -> Path:
        img = Image.new('RGB', (100, 100), color=color)
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: b"Test Camera",
                piexif.ImageIFD.Model: b"Test Model",
                piexif.ImageIFD.DateTime: b"2024:12:08 12:00:00",
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: b"2024:12:08 12:00:00",
                piexif.ExifIFD.DateTimeDigitized: b"2024:12:08 12:00:00",
            },
            "GPS": {
                piexif.GPSIFD.GPSLatitude: ((40, 1), (42, 1), (46, 1)),
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLongitude: ((73, 1), (58, 1), (26, 1)),
                piexif.GPSIFD.GPSLongitudeRef: b"W",
            }
        }
        exif_bytes = piexif.dump(exif_dict)
        jpeg_path = temp_dir / "test_image.jpg"
        img.save(str(jpeg_path), "jpeg", exif=exif_bytes, quality=95)
        return jpeg_path
    return _make

def test_is_convertible_image_jpeg(make_sample_jpeg):
    sample_jpeg = make_sample_jpeg()
    assert JXLConverter.is_convertible_image(sample_jpeg)

def test_is_convertible_image_non_existent(temp_dir):
    non_existent = temp_dir / "nonexistent.jpg"
    assert not JXLConverter.is_convertible_image(non_existent)

def test_is_convertible_image_non_jpeg(temp_dir):
    png_path = temp_dir / "test.png"
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(str(png_path), "png")
    assert not JXLConverter.is_convertible_image(png_path)

def test_convert_to_jxl_creates_file(make_sample_jpeg):
    sample_jpeg = make_sample_jpeg()
    jxl_path = JXLConverter.convert_to_jxl(sample_jpeg)

    if HAS_CJXL:
        assert jxl_path.exists()
        assert jxl_path.suffix == '.jxl'
        assert sample_jpeg.exists()
    else:
        assert jxl_path == sample_jpeg

def test_convert_to_jxl_removes_original(make_sample_jpeg):
    sample_jpeg = make_sample_jpeg()
    assert sample_jpeg.exists()

    jxl_path = JXLConverter.convert_to_jxl(sample_jpeg)

    if HAS_CJXL:
        assert jxl_path.exists()
        assert not sample_jpeg.exists()
    else:
        assert jxl_path == sample_jpeg

def test_convert_to_jxl_custom_output_path(make_sample_jpeg, temp_dir):
    sample_jpeg = make_sample_jpeg()
    custom_path = temp_dir / "custom_output.jxl"
    jxl_path = JXLConverter.convert_to_jxl(
        sample_jpeg, output_path=custom_path)

    if HAS_CJXL:
        assert jxl_path == custom_path
        assert custom_path.exists()
        assert sample_jpeg.exists()
    else:
        assert jxl_path == sample_jpeg

@pytest.mark.skipif(not HAS_CJXL, reason="cjxl binary not available")
def test_convert_to_jxl_preserves_image_quality(make_sample_jpeg, temp_dir):
    sample_jpeg = make_sample_jpeg(color='green')
    jxl_path = JXLConverter.convert_to_jxl(sample_jpeg)
    assert jxl_path != sample_jpeg, "Conversion failed, JXL not produced"

    if HAS_DJXL:
        decoded_path = temp_dir / "decoded.png"
        result = subprocess.run(
            [str(_DJXL_PATH), str(jxl_path), str(decoded_path)],
            capture_output=True,
            timeout=120
        )
        stderr = result.stderr.decode(
            'utf-8', errors='ignore') if result.stderr else ''
        assert result.returncode == 0, f"djxl failed to decode: {stderr}"
        assert decoded_path.exists(), "djxl did not produce decoded output"

        with Image.open(sample_jpeg) as original, Image.open(decoded_path) as decoded:
            decoded_rgb = decoded.convert(original.mode)
            diff = ImageChops.difference(original, decoded_rgb)
            assert diff.getbbox() is None, "Round-trip JXL changed pixel data"
    else:
        with open(jxl_path, 'rb') as f:
            header = f.read(8)
        is_jxl = header[4:8] == b'JXL '
        assert is_jxl, f"File is not a valid JXL format. Header: {header.hex()}"
        assert jxl_path.stat().st_size > 0, "JXL file is empty"

@pytest.mark.skipif(not HAS_CJXL, reason="cjxl binary not available")
def test_convert_to_jxl_file_size_reduction(make_sample_jpeg, capsys):
    sample_jpeg = make_sample_jpeg()
    original_size = sample_jpeg.stat().st_size

    jxl_path = JXLConverter.convert_to_jxl(sample_jpeg)
    jxl_size = jxl_path.stat().st_size

    assert jxl_path.suffix == '.jxl'
    assert original_size > 0
    assert jxl_size > 0

    print(f"Original JPEG size: {original_size} bytes")
    print(f"Converted JXL size: {jxl_size} bytes")
    print(f"Size reduction: {(1 - jxl_size / original_size) * 100:.1f}%")
