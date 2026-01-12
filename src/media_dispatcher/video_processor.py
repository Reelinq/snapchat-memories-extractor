from pathlib import Path
from src.metadata.video_metadata_writer import VideoMetadataWriter
from src.models import Memory
from src.config.main import Config
from src.converters.h265_converter import VideoConverter


def process_video(memory: Memory, file_path: Path, overlay_applied: bool = False):
    write_metadata = Config.from_args().cli_options['write_metadata']
    video_codec = Config.from_args().cli_options['video_codec']

    if write_metadata:
        return VideoMetadataWriter().write_video_metadata(memory, file_path)

    # If overlay was applied, it already re-encoded the video
    if video_codec == 'h265' and not overlay_applied:
        file_path = VideoConverter().run(file_path)

    return file_path
