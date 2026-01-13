from src.memories import Memory
from pathlib import Path
from src.media_dispatcher import process_image, ProcessVideo, ZipProcessor
from src.config import Config


def process_media(memory: Memory, file_path: Path, config: Config):
    if memory.is_zip:
        return ZipProcessor().run(memory, file_path, config)
    if memory.media_type == "Image":
        return process_image(memory, file_path, config)
    else:
        return ProcessVideo().run(memory, file_path, config)
