from src.models import Memory
from pathlib import Path
from src.media_dispatcher.image_processor import process_image
from src.media_dispatcher.video_processor import process_video
from src.media_dispatcher.zip_processor import ZipProcessor
from src.logger.log import log


def process_media(memory: Memory, file_path: Path):
    ext = file_path.suffix.lower()
    if ext == ".jpg":
        process_image(memory, file_path)
    elif ext == ".mov":
        process_video(memory, file_path)
    elif ext == ".zip":
        ZipProcessor.run(memory, file_path)
    else:
        log(f"Unknown file type: {file_path}, skipping processing", "warning")
