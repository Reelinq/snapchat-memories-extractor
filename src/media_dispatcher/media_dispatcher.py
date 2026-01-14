from src.memories import Memory
from pathlib import Path
from src.media_dispatcher.image_processor import process_image
from src.media_dispatcher.video_processor import ProcessVideo
from src.media_dispatcher.zip_processor import ZipProcessor
from src.config import Config


def process_media(memory: Memory, file_path: Path, config: Config):
    if memory.is_zip:
        return ZipProcessor(memory, file_path, config).run()
    if memory.media_type == "Image":
        return process_image(memory, file_path, config)
    else:
        return ProcessVideo(memory, file_path, config).run()
