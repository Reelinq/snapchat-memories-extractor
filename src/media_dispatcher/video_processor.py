from pathlib import Path
from src.metadata import VideoMetadataWriter
from src.memories import Memory
from src.config import Config
from src.converters import VideoConverter


class ProcessVideo:
    def run(self, memory: Memory, file_path: Path, config: Config):
        if config.from_args().cli_options['write_metadata']:
            return VideoMetadataWriter().write_video_metadata(memory, file_path, config)

        if self._should_process_video(config):
            file_path = VideoConverter().run(file_path, config)

        return file_path


    @staticmethod
    def _should_process_video(config):
        if (
            config.from_args().cli_options['video_codec'] != 'h264' or
            config.from_args().cli_options['ffmpeg_preset'] != 'fast' or
            config.from_args().cli_options['ffmpeg_pixel_format'] != 'yuv420p' or
            config.from_args().cli_options['write_metadata'] != True or
            config.from_args().cli_options['crf'] != 23
            ):
            return True
        return False
