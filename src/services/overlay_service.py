from pathlib import Path
from PIL import Image
from io import BytesIO
import re
import subprocess
import tempfile
from imageio_ffmpeg import get_ffmpeg_exe
from concurrent.futures import ProcessPoolExecutor
from typing import Optional
from src.error_handling import handle_errors


def _image_overlay_worker(image_bytes: bytes, overlay_bytes: bytes, quality: int = 95) -> bytes:
    base_image = Image.open(BytesIO(image_bytes))
    overlay_image = Image.open(BytesIO(overlay_bytes))

    if base_image.mode != 'RGBA':
        base_image = base_image.convert('RGBA')

    if overlay_image.mode != 'RGBA':
        overlay_image = overlay_image.convert('RGBA')

    if overlay_image.size != base_image.size:
        overlay_image = overlay_image.resize(
            base_image.size, Image.Resampling.LANCZOS)

    combined_image = Image.alpha_composite(base_image, overlay_image)
    combined_rgb_image = combined_image.convert('RGB')

    output_buffer = BytesIO()
    combined_rgb_image.save(output_buffer, format='JPEG', quality=quality)
    return output_buffer.getvalue()


class OverlayService:
    _ffmpeg_exe_cache = None
    _process_pool: Optional[ProcessPoolExecutor] = None
    _pool_max_workers = 4

    @classmethod
    def _get_ffmpeg_exe(class_reference) -> str:
        if class_reference._ffmpeg_exe_cache is None:
            class_reference._ffmpeg_exe_cache = get_ffmpeg_exe()
        return class_reference._ffmpeg_exe_cache

    @classmethod
    def get_process_pool(class_reference, max_workers: Optional[int] = None) -> ProcessPoolExecutor:
        if class_reference._process_pool is None:
            workers = max_workers or class_reference._pool_max_workers
            class_reference._process_pool = ProcessPoolExecutor(
                max_workers=workers)
        return class_reference._process_pool

    @classmethod
    def shutdown_process_pool(class_reference) -> None:
        if class_reference._process_pool is not None:
            class_reference._process_pool.shutdown(wait=True)
            class_reference._process_pool = None

    @handle_errors(return_on_error=b'')
    def apply_overlay_to_image(self, image_bytes: bytes, overlay_bytes: bytes, jpeg_quality: int = 95, use_process_pool: bool = True) -> bytes:
        if use_process_pool:
            pool = self.get_process_pool()
            future = pool.submit(_image_overlay_worker,
                                 image_bytes, overlay_bytes, jpeg_quality)
            return future.result()
        else:
            return _image_overlay_worker(image_bytes, overlay_bytes, jpeg_quality)

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
