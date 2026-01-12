from pathlib import Path
from src.models import Memory
from src.config.main import Config
from src.zip_processor import ZipProcessor as CoreZipProcessor
from src.overlay.image_composer import ImageComposer
from src.overlay.video_composer import VideoComposer
from src.media_dispatcher.image_processor import process_image
from src.media_dispatcher.video_processor import ProcessVideo


class ZipProcessor:
    def run(self, memory: Memory, file_path: Path):
        apply_overlay = Config.from_args().cli_options['apply_overlay']
        content, overlay, extention = CoreZipProcessor().extract_media_from_zip(file_path)
        output_path = file_path.with_suffix(extention)
        file_path.unlink()

        overlay_applied = False

        if apply_overlay:
            self._apply_overlay(content, overlay, extention, output_path)
            overlay_applied = True
        else:
            self._bytes_to_path(content, output_path)

        if extention == '.jpg':
            return process_image(memory, output_path)

        return ProcessVideo().run(memory, output_path)


    @staticmethod
    def _apply_overlay(content: bytes, overlay: bytes, extention: str, output_path: Path):
        if extention == '.jpg':
            ImageComposer().apply_overlay(content, overlay, output_path)
        else:
            VideoComposer().apply_overlay(content, overlay, output_path)


    @staticmethod
    def _bytes_to_path(bytes_content: bytes, output_path: Path) -> Path:
        with open(output_path, "wb") as file:
            file.write(bytes_content)
