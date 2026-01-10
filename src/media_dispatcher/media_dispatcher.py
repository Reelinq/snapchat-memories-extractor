from src.models import Memory
from pathlib import Path
from src.media_dispatcher.image_processor import process_image
from src.media_dispatcher.video_processor import process_video
from src.media_dispatcher.zip_processor import ZipProcessor


def process_media(memory: Memory, file_path: Path):
    if memory.is_zip:
        ZipProcessor.run(memory, file_path)
        return
    if memory.media_type == "Image":
        process_image(memory, file_path)
    else:
        process_video(memory, file_path)
