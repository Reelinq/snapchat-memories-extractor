from zipfile import ZipFile
from typing import Optional
from src.config import Config


class ZipProcessor:
    def __init__(self, file_path: str, config: Config):
        self.file_path = file_path
        self.config = config


    def extract_media_from_zip(self) -> tuple[Optional[bytes], Optional[str], Optional[bytes]]:
        with ZipFile(self.file_path, 'r') as zip_file:
            result = self._read_files(zip_file)
        return result


    def _read_files(self, zip_file: ZipFile):
        extract_overlay = self.config.from_args().cli_options['apply_overlay']

        overlay_file_name = self._find_file(zip_file, find_png=True)
        media_file_name = self._find_file(zip_file, find_png=False)

        media_overlay = None
        if extract_overlay:
            media_overlay = zip_file.read(overlay_file_name)

        media_content = zip_file.read(media_file_name)
        media_extension = self._get_extension(media_file_name)

        return media_content, media_overlay, media_extension


    def _find_file(self, zip_file: ZipFile, find_png: bool) -> Optional[str]:
        for name in zip_file.namelist():
            result = self._is_png_file(name, find_png)
            if result:
                return result
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
