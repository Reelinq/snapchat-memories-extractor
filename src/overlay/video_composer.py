from pathlib import Path
from PIL import Image
from io import BytesIO
import subprocess
import tempfile
from imageio_ffmpeg import get_ffmpeg_exe
from src import config
from src.error_handling import handle_errors

#TODO: Image overlay returns bytes, video overlay writes to file. Make consistent.

class VideoComposer:
    @handle_errors(return_on_error=None)
    def apply_overlay(self, video_bytes: bytes, overlay_bytes: bytes, output_path: Path) -> None:
        # FFMPEG can't read from memory, so we need to write to temp files
        video_temporary_file_path = self._write_video_to_temp_file(video_bytes, '.mp4')
        video_width, video_height = self._get_video_dimensions(video_temporary_file_path)

        overlay_image = Image.open(BytesIO(overlay_bytes))
        # In some cases the overlay image is mismatched by 1 pixel
        overlay_image = self._resize_to_match(overlay_image, (video_width, video_height))
        overlay_temporary_file_path = self._write_overlay_to_temp_file(overlay_image)

        ffmpeg_command = self._build_ffmpeg_overlay_command(video_temporary_file_path, overlay_temporary_file_path, (output_path))
        ffmpeg_timeout = config.cli_options['ffmpeg_timeout']
        self._run_ffmpeg_command(ffmpeg_command, ffmpeg_timeout)
        self._cleanup_temp_files(video_temporary_file_path, overlay_temporary_file_path)


    @staticmethod
    def _write_video_to_temp_file(data: bytes, suffix: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(data)
            return temp_file.name


    @staticmethod
    def _get_video_dimensions(video_path) -> tuple[int, int]:
        ffprobe_response = subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height', '-of', 'csv=p=0', video_path
        ], text=True)
        return tuple(map(int, ffprobe_response.strip().split(',')))


    @staticmethod
    def _resize_to_match(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
        if image.size != target_size:
            return image.resize(target_size, Image.Resampling.LANCZOS)
        return image


    @staticmethod
    def _write_overlay_to_temp_file(overlay_image: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as overlay_temporary_file:
            overlay_image.save(overlay_temporary_file, format='PNG')
            return overlay_temporary_file.name


    def _build_ffmpeg_overlay_command(self, video_path: str, overlay_path: str, output_path: Path) -> list:
        return [
            get_ffmpeg_exe(),
            '-i', video_path,
            '-i', overlay_path,
            '-filter_complex', 'overlay=0:0',
            '-c:v', self._get_video_codec(),
            '-preset', 'fast',
            '-crf', str(self._get_video_crf()),
            '-pix_fmt', 'yuv420p',
            '-c:a', 'copy',
            '-movflags', '+faststart',
            str(output_path)
        ]


    @staticmethod
    def _get_video_codec():
        if config.cli_options['video_codec'] == 'h265':
            return 'libx265'
        return 'libx264'


    @staticmethod
    def _get_video_crf():
        user_crf = getattr(config.cli_options, 'crf', None)
        if user_crf == None:
            return 23 if config.cli_options['video_codec'] == 'h264' else 28
        return user_crf


    @staticmethod
    def _run_ffmpeg_command(command: list, timeout: int):
        return subprocess.run(
            command,
            check=True,
            timeout=timeout,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(
                subprocess, 'CREATE_NO_WINDOW') else 0
        )


    @staticmethod
    def _cleanup_temp_files(video_temporary_file_path: str, overlay_temporary_file_path: str):
        Path(video_temporary_file_path).unlink(missing_ok=True)
        Path(overlay_temporary_file_path).unlink(missing_ok=True)
