import subprocess
from pathlib import Path

from imageio_ffmpeg import get_ffmpeg_exe

from src.config import Config


class VideoConverter:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def run(self) -> Path:
        command = self._build_ffmpeg_command()
        subprocess.run(command)
        return self.file_path

    def _build_ffmpeg_command(self) -> list:
        return [
            get_ffmpeg_exe(),
            "-y",
            "-i",
            str(self.file_path),
            "-c:a",
            "copy",
            "-c:v",
            self._get_video_codec(),
            "-crf",
            self._get_video_crf(),
            "-preset",
            self._get_ffmpeg_preset(),
            "-pix_fmt",
            self._get_video_pixel_format(),
            str(self.file_path),
        ]

    def _get_video_codec(self) -> str:
        if Config.cli_options["video_codec"] == "h265":
            return "libx265"
        return "libx264"

    @staticmethod
    def _get_video_crf() -> str:
        user_crf = Config.cli_options.get("crf", None)
        if user_crf is None:
            return "23" if Config.cli_options["video_codec"] == "h264" else "28"
        return str(user_crf)

    def _get_ffmpeg_preset(self) -> str:
        return Config.cli_options["ffmpeg_preset"]

    def _get_video_pixel_format(self) -> str:
        return Config.cli_options["ffmpeg_pixel_format"]
