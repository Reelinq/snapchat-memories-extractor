import unittest
from src.processors.zip_processor import *
import zipfile
from io import BytesIO

class TestZipProcessor(unittest.TestCase):
    def test_is_zip(self):
        content = b'PK\x03\x04dummyzipcontent'
        self.assertTrue(ZipProcessor.is_zip(content, 'application/zip'))
        self.assertTrue(ZipProcessor.is_zip(content, 'something/zip'))
        self.assertTrue(ZipProcessor.is_zip(content, 'other'))  # magic bytes
        self.assertFalse(ZipProcessor.is_zip(b'notazip', 'text/plain'))

    def test_extract_media_from_zip(self):
        # Create a zip in memory with a jpg and png
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('test.jpg', b'jpgdata')
            zf.writestr('overlay.png', b'pngdata')
        content = buf.getvalue()
        media, ext, overlay = ZipProcessor.extract_media_from_zip(content)
        self.assertEqual(media, b'jpgdata')
        self.assertEqual(ext, '.jpg')
        self.assertEqual(overlay, b'pngdata')

        # Create a zip in memory with a mp4 and png
        buf2 = BytesIO()
        with zipfile.ZipFile(buf2, 'w') as zf:
            zf.writestr('video.mp4', b'mp4data')
            zf.writestr('overlay.png', b'pngdata2')
        content2 = buf2.getvalue()
        media2, ext2, overlay2 = ZipProcessor.extract_media_from_zip(content2)
        self.assertEqual(media2, b'mp4data')
        self.assertEqual(ext2, '.mp4')
        self.assertEqual(overlay2, b'pngdata2')

if __name__ == "__main__":
    unittest.main()
