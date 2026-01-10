from pathlib import Path
from src.metadata.video_metadata_writer import VideoMetadataWriter
from src.models import Memory
from src.config.main import Config


def process_video(memory: Memory, file_path: Path):
    write_metadata = Config.from_args().cli_options['write_metadata']

    if write_metadata:
        return VideoMetadataWriter().write_video_metadata(memory, file_path)

    return file_path
