from src.models import Memory
from pathlib import Path
from src.config.main import Config
from src.metadata.image_metadata_writer import ImageMetadataWriter
from src.metadata.video_metadata_writer import VideoMetadataWriter


class MetadataDispatcher:
    def write_metadata(self, memory: Memory, file_path: Path, is_image: bool):
        if is_image:
            ImageMetadataWriter().write_image_metadata(memory, file_path)
        else:
            VideoMetadataWriter().write_video_metadata(memory, file_path)
