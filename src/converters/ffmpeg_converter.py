from pathlib import Path
import subprocess
from imageio_ffmpeg import get_ffmpeg_exe
from src.config import Config


class VideoConverter:
    def __init__(self, config: Config):
        self.config = config


    def run(self, file_path: Path) -> Path:
        command = self._build_ffmpeg_command(file_path)
        subprocess.run(command)
        return file_path


    def _build_ffmpeg_command(self, file_path) -> list:
        return [
            get_ffmpeg_exe(),
            '-y',
            '-i', str(file_path),
            '-c:a', 'copy',
            '-c:v', self._get_video_codec(),
            '-crf', self._get_video_crf(),
            '-preset', self._get_ffmpeg_preset(),
            '-pix_fmt', self._get_video_pixel_format(),
            str(file_path)
        ]


    def _get_video_codec(self) -> str:
        if self.config.cli_options['video_codec'] == 'h265':
            return 'libx265'
        return 'libx264'


    def _get_video_crf(self) -> str:
        user_crf = getattr(self.config.cli_options, 'crf', None)
        if user_crf == None:
            return "23" if self.config.cli_options['video_codec'] == 'h264' else "28"
        return str(user_crf)


    def _get_ffmpeg_preset(self) -> str:
        return self.config.cli_options['ffmpeg_preset']


    def _get_video_pixel_format(self) -> str:
        return self.config.cli_options['ffmpeg_pixel_format']
