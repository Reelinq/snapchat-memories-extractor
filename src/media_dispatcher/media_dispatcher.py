from src.models import Memory
from pathlib import Path
import src.media_dispatcher.video_processor
from src.media_dispatcher.image_processor import ImageProcessor
from src.media_dispatcher.video_processor import VideoProcessor
from src.media_dispatcher.zip_processor import ZipProcessor


class MediaDispatcher:
    def process_media(self, memory: Memory, file_path: Path):
        if memory.media_type == "Image":
            ImageProcessor.process_image(memory, file_path)
        elif memory.media_type == "Video":
            VideoProcessor.process_video(memory, file_path)
        else:
            ZipProcessor.process_zip(memory, file_path)
