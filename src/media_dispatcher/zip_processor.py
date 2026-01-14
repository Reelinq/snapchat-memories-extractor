from pathlib import Path
from src.memories import Memory
from src.config import Config
from src import ZipProcessor as CoreZipProcessor
from src.overlay import *
from src.media_dispatcher.image_processor import process_image
from src.media_dispatcher.video_processor import ProcessVideo


class ZipProcessor:
    def __init__(self, memory: Memory, file_path: Path, config: Config):
        self.memory = memory
        self.file_path = file_path
        self.config = config


    def run(self):
        apply_overlay = self.config.from_args().cli_options['apply_overlay']
        content, overlay, extention = CoreZipProcessor(self.file_path, self.config).extract_media_from_zip()
        output_path = self.file_path.with_suffix(extention)
        self.file_path.unlink()
        overlay_applied = False

        if apply_overlay:
            self._apply_overlay(content, overlay, extention, output_path)
            overlay_applied = True
        else:
            self._bytes_to_path(content, output_path)

        if extention == '.jpg':
            return process_image(self.memory, output_path, self.config)

        return ProcessVideo(self.memory, output_path, self.config).run()


    def _apply_overlay(self, content: bytes, overlay: bytes, extention: str, output_path: Path):
        if extention == '.jpg':
            ImageComposer().apply_overlay(content, overlay, output_path, self.config)
        else:
            VideoComposer().apply_overlay(content, overlay, output_path, self.config)


    @staticmethod
    def _bytes_to_path(bytes_content: bytes, output_path: Path) -> Path:
        with open(output_path, "wb") as file:
            file.write(bytes_content)
