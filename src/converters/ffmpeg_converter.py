from pathlib import Path
import subprocess
from imageio_ffmpeg import get_ffmpeg_exe
from src.config.main import Config


class VideoConverter:
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


    @staticmethod
    def _get_video_codec() -> str:
        if Config.from_args().cli_options['video_codec'] == 'h265':
            return 'libx265'
        return 'libx264'


    @staticmethod
    def _get_video_crf() -> str:
        user_crf = getattr(Config.from_args().cli_options, 'crf', None)
        if user_crf == None:
            return "23" if Config.from_args().cli_options['video_codec'] == 'h264' else "28"
        return str(user_crf)


    @staticmethod
    def _get_ffmpeg_preset() -> str:
        return Config.from_args().cli_options['ffmpeg_preset']


    @staticmethod
    def _get_video_pixel_format() -> str:
        return Config.from_args().cli_options['ffmpeg_pixel_format']
