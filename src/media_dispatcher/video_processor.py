from pathlib import Path
from src.metadata import VideoMetadataWriter
from src.memories import Memory
from src.config import Config
from src.converters import VideoConverter


class ProcessVideo:
    def __init__(self, memory: Memory, file_path: Path, config: Config):
        self.memory = memory
        self.file_path = file_path
        self.config = config


    def run(self):
        if self.config.cli_options['write_metadata']:
            return VideoMetadataWriter(self.memory, self.file_path, self.config).write_video_metadata()

        if self._should_process_video():
            file_path = VideoConverter(self.config).run(self.file_path)

        return file_path


    def _should_process_video(self):
        if (
            self.config.cli_options['video_codec'] != 'h264' or
            self.config.cli_options['ffmpeg_preset'] != 'fast' or
            self.config.cli_options['ffmpeg_pixel_format'] != 'yuv420p' or
            self.config.cli_options['write_metadata'] != True or
            self.config.cli_options['crf'] != 23
            ):
            return True
        return False
