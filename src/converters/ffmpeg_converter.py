from pathlib import Path
import subprocess
from imageio_ffmpeg import get_ffmpeg_exe
from src.config import Config


class VideoConverter:
    def run(self, file_path: Path, config: Config) -> Path:
        command = self._build_ffmpeg_command(file_path, config)
        subprocess.run(command)
        return file_path


    def _build_ffmpeg_command(self, file_path, config: Config) -> list:
        return [
            get_ffmpeg_exe(),
            '-y',
            '-i', str(file_path),
            '-c:a', 'copy',
            '-c:v', self._get_video_codec(config),
            '-crf', self._get_video_crf(config),
            '-preset', self._get_ffmpeg_preset(config),
            '-pix_fmt', self._get_video_pixel_format(config),
            str(file_path)
        ]


    @staticmethod
    def _get_video_codec(config) -> str:
        if config.from_args().cli_options['video_codec'] == 'h265':
            return 'libx265'
        return 'libx264'


    @staticmethod
    def _get_video_crf(config) -> str:
        user_crf = getattr(config.from_args().cli_options, 'crf', None)
        if user_crf == None:
            return "23" if config.from_args().cli_options['video_codec'] == 'h264' else "28"
        return str(user_crf)


    @staticmethod
    def _get_ffmpeg_preset(config) -> str:
        return config.from_args().cli_options['ffmpeg_preset']


    @staticmethod
    def _get_video_pixel_format(config) -> str:
        return config.from_args().cli_options['ffmpeg_pixel_format']
