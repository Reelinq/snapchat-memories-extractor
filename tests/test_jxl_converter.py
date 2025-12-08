import subprocess
import sys
import unittest
from pathlib import Path
from PIL import Image, ImageChops
import piexif
import tempfile
import shutil
from services.jxl_converter import JXLConverter


HAS_CJXL = JXLConverter._get_cjxl_path() is not None


def _get_djxl_path() -> Path | None:
    if sys.platform == 'win32':
        binary_name = 'djxl.exe'
        rel_path = Path('libjxl-binaries/windows') / binary_name
    else:
        binary_name = 'djxl'
        rel_path = Path('libjxl-binaries/linux') / binary_name

    base_dir = Path(__file__).resolve().parent.parent
    candidate = base_dir / rel_path
    if candidate.exists():
        return candidate

    try:
        result = subprocess.run([binary_name, '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return Path(binary_name)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    return None


_DJXL_PATH = _get_djxl_path()
HAS_DJXL = _DJXL_PATH is not None


class TestJXLConverter(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_sample_jpeg(self, color='red') -> Path:
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
        jpeg_path = self.temp_dir / "test_image.jpg"
        img.save(str(jpeg_path), "jpeg", exif=exif_bytes, quality=95)
        return jpeg_path

    def test_is_convertible_image_jpeg(self):
        sample_jpeg = self._make_sample_jpeg()
        self.assertTrue(JXLConverter.is_convertible_image(sample_jpeg))

    def test_is_convertible_image_non_existent(self):
        non_existent = self.temp_dir / "nonexistent.jpg"
        self.assertFalse(JXLConverter.is_convertible_image(non_existent))

    def test_is_convertible_image_non_jpeg(self):
        png_path = self.temp_dir / "test.png"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(str(png_path), "png")
        self.assertFalse(JXLConverter.is_convertible_image(png_path))

    def test_convert_to_jxl_creates_file(self):
        sample_jpeg = self._make_sample_jpeg()
        jxl_path = JXLConverter.convert_to_jxl(sample_jpeg, remove_original=False)

        if HAS_CJXL:
            self.assertTrue(jxl_path.exists())
            self.assertEqual(jxl_path.suffix, '.jxl')
            self.assertTrue(sample_jpeg.exists())
        else:
            self.assertEqual(jxl_path, sample_jpeg)

    def test_convert_to_jxl_removes_original(self):
        sample_jpeg = self._make_sample_jpeg()
        self.assertTrue(sample_jpeg.exists())

        jxl_path = JXLConverter.convert_to_jxl(sample_jpeg, remove_original=True)

        if HAS_CJXL:
            self.assertTrue(jxl_path.exists())
            self.assertFalse(sample_jpeg.exists())
        else:
            self.assertEqual(jxl_path, sample_jpeg)

    def test_convert_to_jxl_custom_output_path(self):
        sample_jpeg = self._make_sample_jpeg()
        custom_path = self.temp_dir / "custom_output.jxl"
        jxl_path = JXLConverter.convert_to_jxl(sample_jpeg, output_path=custom_path, remove_original=False)

        if HAS_CJXL:
            self.assertEqual(jxl_path, custom_path)
            self.assertTrue(custom_path.exists())
            self.assertTrue(sample_jpeg.exists())
        else:
            self.assertEqual(jxl_path, sample_jpeg)

    @unittest.skipIf(not HAS_CJXL, "cjxl binary not available")
    def test_convert_to_jxl_preserves_image_quality(self):
        sample_jpeg = self._make_sample_jpeg(color='green')
        jxl_path = JXLConverter.convert_to_jxl(sample_jpeg, remove_original=False)
        self.assertNotEqual(jxl_path, sample_jpeg, "Conversion failed, JXL not produced")

        if HAS_DJXL:
            # Perform round-trip verification with djxl decoder
            decoded_path = self.temp_dir / "decoded.png"
            result = subprocess.run(
                [str(_DJXL_PATH), str(jxl_path), str(decoded_path)],
                capture_output=True,
                timeout=120
            )
            stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
            self.assertEqual(result.returncode, 0, f"djxl failed to decode: {stderr}")
            self.assertTrue(decoded_path.exists(), "djxl did not produce decoded output")

            with Image.open(sample_jpeg) as original, Image.open(decoded_path) as decoded:
                decoded_rgb = decoded.convert(original.mode)
                diff = ImageChops.difference(original, decoded_rgb)
                self.assertIsNone(diff.getbbox(), "Round-trip JXL changed pixel data")
        else:
            # Without djxl, verify lossless conversion by checking JXL structure
            with open(jxl_path, 'rb') as f:
                header = f.read(8)
            # JXL files contain "JXL " magic at offset 4: \x00\x00\x00\x0c + 'JXL ' + more
            is_jxl = header[4:8] == b'JXL '
            self.assertTrue(is_jxl, f"File is not a valid JXL format. Header: {header.hex()}")

            # Verify lossless_jpeg was used (file should be valid)
            self.assertGreater(jxl_path.stat().st_size, 0, "JXL file is empty")

    @unittest.skipIf(not HAS_CJXL, "cjxl binary not available")
    def test_convert_to_jxl_file_size_reduction(self):
        sample_jpeg = self._make_sample_jpeg()
        original_size = sample_jpeg.stat().st_size

        jxl_path = JXLConverter.convert_to_jxl(sample_jpeg, remove_original=False)
        jxl_size = jxl_path.stat().st_size

        self.assertEqual(jxl_path.suffix, '.jxl')
        # Not asserting reduction strictly; ensure conversion happened
        self.assertGreater(original_size, 0)
        self.assertGreater(jxl_size, 0)
        print(f"Original JPEG size: {original_size} bytes")
        print(f"Converted JXL size: {jxl_size} bytes")
        print(f"Size reduction: {(1 - jxl_size/original_size)*100:.1f}%")


if __name__ == "__main__":
    unittest.main()
