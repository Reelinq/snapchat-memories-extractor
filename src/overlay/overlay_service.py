from pathlib import Path
from PIL import Image
from io import BytesIO
import re
import subprocess
import tempfile
from imageio_ffmpeg import get_ffmpeg_exe
from typing import Optional
from src.error_handling import handle_errors


class OverlayService:
    _ffmpeg_exe_cache = None

    @classmethod
    def _get_ffmpeg_exe(class_reference) -> str:
        if class_reference._ffmpeg_exe_cache is None:
            class_reference._ffmpeg_exe_cache = get_ffmpeg_exe()
        return class_reference._ffmpeg_exe_cache

    @handle_errors(return_on_error=None)
    def apply_overlay_to_video(self, video_bytes: bytes, overlay_bytes: bytes, output_path: Path, ffmpeg_timeout: int = 60) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as video_temporary_file:
            video_temporary_file.write(video_bytes)
            video_temporary_file_path = video_temporary_file.name

        overlay_temporary_file_path = None

        ffmpeg_exe = self._get_ffmpeg_exe()
        probe_command = [
            ffmpeg_exe,
            '-i', video_temporary_file_path,
            '-hide_banner'
        ]

        probe_result = subprocess.run(
            probe_command,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(
                subprocess, 'CREATE_NO_WINDOW') else 0
        )

        video_dimensions_match = re.search(
            r'(\d{2,5})x(\d{2,5})', probe_result.stderr)
        if not video_dimensions_match:
            raise Exception("Could not determine video dimensions")

        video_width = int(video_dimensions_match.group(1))
        video_height = int(video_dimensions_match.group(2))

        overlay_image = Image.open(BytesIO(overlay_bytes))

        if overlay_image.size != (video_width, video_height):
            overlay_image = overlay_image.resize(
                (video_width, video_height), Image.Resampling.LANCZOS)

        overlay_buffer = BytesIO()
        overlay_image.save(overlay_buffer, format='PNG')
        overlay_buffer.seek(0)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as overlay_temporary_file:
            overlay_temporary_file.write(overlay_buffer.read())
            overlay_temporary_file_path = overlay_temporary_file.name

        command = [
            ffmpeg_exe,
            '-i', video_temporary_file_path,
            '-i', overlay_temporary_file_path,
            '-filter_complex', 'overlay=0:0',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'copy',
            '-movflags', '+faststart',
            '-y',
            str(output_path)
        ]

        subprocess_execution_result = subprocess.run(
            command,
            check=True,
            timeout=ffmpeg_timeout,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(
                subprocess, 'CREATE_NO_WINDOW') else 0
        )

        Path(video_temporary_file_path).unlink(missing_ok=True)
        if overlay_temporary_file_path is not None:
            Path(overlay_temporary_file_path).unlink(missing_ok=True)
