import zipfile
from io import BytesIO
from typing import Optional

class ZipProcessor:
    @staticmethod
    def is_zip(content: bytes, content_type: str) -> bool:
        if 'zip' in content_type.lower():
            return True

        # Check magic bytes
        if len(content) >= 4 and content[:4] == b'PK\x03\x04':
            return True

        return False


    @staticmethod
    def extract_media_from_zip(content: bytes, extract_overlay: bool = True) -> tuple[bytes, str, Optional[bytes]]:
        with zipfile.ZipFile(BytesIO(content)) as zip_file:
            media_bytes = None
            extension = None
            overlay_png = None

            for filename in zip_file.namelist():
                lower = filename.lower()
                if lower.endswith(('.jpg', '.jpeg')):
                    media_bytes = zip_file.read(filename)
                    extension = '.jpg'
                elif lower.endswith('.mp4'):
                    media_bytes = zip_file.read(filename)
                    extension = '.mp4'
                elif extract_overlay and lower.endswith('.png'):
                    overlay_png = zip_file.read(filename)

            return media_bytes, extension, overlay_png
