from pathlib import Path
from src.metadata.video_metadata_writer import VideoMetadataWriter
from src.models import Memory
from src.config.main import Config
from src.converters.ffmpeg_converter import VideoConverter

class ProcessVideo:
    def run(self, memory: Memory, file_path: Path):
        if Config.from_args().cli_options['write_metadata']:
            return VideoMetadataWriter().write_video_metadata(memory, file_path)

        if self._should_process_video():
            file_path = VideoConverter().run(file_path)

        return file_path


    def _should_process_video(self):
        if (
            self.cli['video_codec'] != 'h264' or
            self.cli['ffmpeg_preset'] != 'fast' or
            self.cli['ffmpeg_pixel_format'] != 'yuv420p' or
            self.cli['write_metadata'] != True or
            self.cli['crf'] != 23
            ):
            return True
        return False
