from pathlib import Path
import subprocess
from src.config.ffmpeg_crf import get_video_crf


class VideoConverter:
    def run(self, file_path: Path) -> Path:
        command = self._build_ffmpeg_command(file_path)
        subprocess.run(command)
        return file_path


    def _build_ffmpeg_command(self, file_path) -> list:
        return [
            "ffmpeg",
            "-y",
            "-i", str(file_path),
            "-c:v", "libx265",
            "-c:a", "copy",
            "-crf", get_video_crf(),
            str(file_path)
        ]
