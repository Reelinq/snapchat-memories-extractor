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
            jpeg_filenames = [filename for filename in zip_file.namelist() if filename.lower().endswith(('.jpg', '.jpeg'))]
            mp4_filenames = [filename for filename in zip_file.namelist() if filename.lower().endswith('.mp4')]

            # Extract overlay PNG only if requested
            overlay_png = None
            if extract_overlay:
                png_filenames = [filename for filename in zip_file.namelist() if filename.lower().endswith('.png')]
                overlay_png = zip_file.read(png_filenames[0])

            if jpeg_filenames:
                return zip_file.read(jpeg_filenames[0]), '.jpg', overlay_png
            elif mp4_filenames:
                return zip_file.read(mp4_filenames[0]), '.mp4', overlay_png
            else:
                raise Exception("ZIP did not contain a JPG or MP4 file")
