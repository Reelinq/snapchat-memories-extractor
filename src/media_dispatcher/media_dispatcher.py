from src.memories import Memory
from pathlib import Path
from src.media_dispatcher import process_image, ProcessVideo, ZipProcessor


def process_media(memory: Memory, file_path: Path):
    if memory.is_zip:
        return ZipProcessor().run(memory, file_path)
    if memory.media_type == "Image":
        return process_image(memory, file_path)
    else:
        return ProcessVideo().run(memory, file_path)
