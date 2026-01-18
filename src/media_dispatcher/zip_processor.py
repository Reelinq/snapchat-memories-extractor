from pathlib import Path

from src import ZipProcessor as CoreZipProcessor
from src.config import Config
from src.media_dispatcher.image_processor import process_image
from src.media_dispatcher.video_processor import ProcessVideo
from src.memories import Memory
from src.overlay import *


class ZipProcessor:
    def __init__(self, memory: Memory, file_path: Path):
        self.memory = memory
        self.file_path = file_path

    def run(self):
        apply_overlay = Config.cli_options["apply_overlay"]
        content, overlay, extention = CoreZipProcessor(
            self.file_path,
        ).extract_media_from_zip()
        output_path = self.file_path.with_suffix(extention)
        self.file_path.unlink()
        overlay_applied = False

        if apply_overlay:
            self._apply_overlay(content, overlay, extention, output_path)
            overlay_applied = True
        else:
            self._bytes_to_path(content, output_path)

        if extention == ".jpg":
            return process_image(self.memory, output_path)

        return ProcessVideo().run(self.memory, output_path)

    def _apply_overlay(
        self, content: bytes, overlay: bytes, extention: str, output_path: Path,
    ):
        if extention == ".jpg":
            ImageComposer(content, overlay, output_path).apply_overlay()
        else:
            VideoComposer(content, overlay, output_path).apply_overlay()

    @staticmethod
    def _bytes_to_path(bytes_content: bytes, output_path: Path) -> Path:
        with open(output_path, "wb") as file:
            file.write(bytes_content)
