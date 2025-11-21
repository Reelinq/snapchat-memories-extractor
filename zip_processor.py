import zipfile
from io import BytesIO
from typing import Optional
from pathlib import Path
from PIL import Image
import re
import subprocess
import tempfile
from imageio_ffmpeg import get_ffmpeg_exe

class ZipProcessor:
    @staticmethod
    def is_zip(content: bytes, content_type: str) -> bool:
        if 'zip' in content_type.lower():
            return True

        # Check magic bytes
        if len(content) >= 4 and content[:4] == b'PK\x03\x04':
            return True

        return False


    @staticmethod
    def extract_media_from_zip(content: bytes, extract_overlay: bool = True) -> tuple[bytes, str, Optional[bytes]]:
        with zipfile.ZipFile(BytesIO(content)) as zf:
            jpg_names = [n for n in zf.namelist() if n.lower().endswith(('.jpg', '.jpeg'))]
            mp4_names = [n for n in zf.namelist() if n.lower().endswith('.mp4')]

            # Extract overlay PNG only if requested
            overlay_png = None
            if extract_overlay:
                png_names = [n for n in zf.namelist() if n.lower().endswith('.png')]
                overlay_png = zf.read(png_names[0])

            if jpg_names:
                return zf.read(jpg_names[0]), '.jpg', overlay_png
            elif mp4_names:
                return zf.read(mp4_names[0]), '.mp4', overlay_png
            else:
                raise Exception("ZIP did not contain a JPG or MP4 file")


    @staticmethod
    def apply_overlay_to_image(image_bytes: bytes, overlay_bytes: bytes) -> bytes:
        base_image = Image.open(BytesIO(image_bytes))
        overlay_image = Image.open(BytesIO(overlay_bytes))

        # Convert base to RGBA if needed for compositing
        if base_image.mode != 'RGBA':
            base_image = base_image.convert('RGBA')

        # Ensure overlay has alpha channel
        if overlay_image.mode != 'RGBA':
            overlay_image = overlay_image.convert('RGBA')

        # Resize overlay to match base image size if needed
        if overlay_image.size != base_image.size:
            overlay_image = overlay_image.resize(base_image.size, Image.Resampling.LANCZOS)

        # Composite the images
        combined = Image.alpha_composite(base_image, overlay_image)

        # Convert back to RGB for JPEG
        combined_rgb = combined.convert('RGB')

        # Save to bytes
        output = BytesIO()
        combined_rgb.save(output, format='JPEG', quality=95)
        return output.getvalue()


    @staticmethod
    def apply_overlay_to_video(video_bytes: bytes, overlay_bytes: bytes, output_path: Path, ffmpeg_timeout: int = 60) -> None:
        # Create temporary files for video and overlay
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as video_temp:
            video_temp.write(video_bytes)
            video_temp_path = video_temp.name

        try:
            # Get video dimensions using ffmpeg
            ffmpeg_exe = get_ffmpeg_exe()
            probe_cmd = [
                ffmpeg_exe,
                '-i', video_temp_path,
                '-hide_banner'
            ]

            probe_result = subprocess.run(
                probe_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )

            # Parse dimensions from stderr
            match = re.search(r'(\d{2,5})x(\d{2,5})', probe_result.stderr)
            if match:
                video_width = int(match.group(1))
                video_height = int(match.group(2))
            else:
                raise Exception("Could not determine video dimensions")

            # Resize overlay PNG to match video dimensions
            overlay_image = Image.open(BytesIO(overlay_bytes))
            if overlay_image.size != (video_width, video_height):
                overlay_image = overlay_image.resize((video_width, video_height), Image.Resampling.LANCZOS)

            # Save resized overlay
            overlay_buffer = BytesIO()
            overlay_image.save(overlay_buffer, format='PNG')
            overlay_buffer.seek(0)

            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as overlay_temp:
                overlay_temp.write(overlay_buffer.read())
                overlay_temp_path = overlay_temp.name

            # Now apply overlay with filter
            cmd = [
                ffmpeg_exe,
                '-i', video_temp_path,
                '-i', overlay_temp_path,
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

            result = subprocess.run(
                cmd,
                check=True,
                timeout=ffmpeg_timeout,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg overlay failed: {e.stderr.decode('utf-8', errors='ignore')}")
        finally:
            # Clean up temp files
            Path(video_temp_path).unlink(missing_ok=True)
            if 'overlay_temp_path' in locals():
                Path(overlay_temp_path).unlink(missing_ok=True)
