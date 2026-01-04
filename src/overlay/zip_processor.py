from zipfile import ZipFile
from io import BytesIO
from typing import Optional


class ZipProcessor:
    @staticmethod
    def is_zip(content: bytes, content_type: str) -> bool:
        if 'zip' in content_type.lower():
            return True
        return content.startswith(b'PK\x03\x04')

    def extract_media_from_zip(self,
        content: bytes, extract_overlay: bool
    ) -> tuple[Optional[bytes], Optional[str], Optional[bytes]]:
        zip_file = ZipFile(BytesIO(content))
        result = self._read_files(zip_file, extract_overlay)
        zip_file.close()
        return result

    def _read_files(self, zip_file: ZipFile, extract_overlay: bool):
        overlay_file_name = self._find_file(zip_file, find_png=True)
        media_file_name = self._find_file(zip_file, find_png=False)

        media_overlay = None
        if overlay_file_name and extract_overlay:
            media_overlay = zip_file.read(overlay_file_name)

        media_content = None
        media_extension = None
        if media_file_name:
            media_content = zip_file.read(media_file_name)
            media_extension = self._get_extension(media_file_name)

        return media_content, media_extension, media_overlay

    def _find_file(self, zip_file: ZipFile, find_png: bool) -> Optional[str]:
        for name in zip_file.namelist():
            return self._is_png_file(name, find_png)
        return None

    @staticmethod
    def _is_png_file(filename: str, find_png: bool) -> bool:
        is_png_extension = filename.lower().endswith('.png')
        if is_png_extension == find_png:
            return filename
        return None

    @staticmethod
    def _get_extension(filename: str) -> str:
        return '.mp4' if filename.lower().endswith('.mp4') else '.jpg'
