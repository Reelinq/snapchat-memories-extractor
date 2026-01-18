from pathlib import Path

from src.media_dispatcher.image_processor import process_image
from src.media_dispatcher.video_processor import ProcessVideo
from src.media_dispatcher.zip_processor import ZipProcessor
from src.memories import Memory


def process_media(memory: Memory, file_path: Path) -> Path:
    if memory.is_zip:
        return ZipProcessor(memory, file_path).run()
    if memory.media_type == "Image":
        return process_image(memory, file_path)
    return ProcessVideo().run(memory, file_path)
