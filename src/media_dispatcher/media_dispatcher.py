from src.memory_model import Memory
from pathlib import Path
from src.media_dispatcher.image_processor import process_image
from src.media_dispatcher.video_processor import ProcessVideo
from src.media_dispatcher.zip_processor import ZipProcessor


def process_media(memory: Memory, file_path: Path):
    if memory.is_zip:
        return ZipProcessor().run(memory, file_path)
    if memory.media_type == "Image":
        return process_image(memory, file_path)
    else:
        return ProcessVideo().run(memory, file_path)
