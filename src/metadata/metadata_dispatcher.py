from src.models import Memory
from pathlib import Path
from src.config.main import Config
from src.metadata.image_metadata_writer import ImageMetadataWriter
from src.metadata.video_metadata_writer import VideoMetadataWriter


class MetadataDispatcher:
    def write_metadata(self, memory: Memory, file_path: Path, is_image: bool):
        ffmpeg_timeout = Config.from_args().cli_options['ffmpeg_timeout']
        jpeg_quality = Config.from_args().cli_options['jpeg_quality']

        if is_image:
            ImageMetadataWriter().write_image_metadata(memory, file_path, jpeg_quality)
        else:
            VideoMetadataWriter().write_video_metadata(memory, file_path, ffmpeg_timeout)
