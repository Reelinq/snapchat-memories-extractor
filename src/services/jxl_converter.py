from pathlib import Path
from PIL import Image
from typing import Optional
import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

class JXLConverter:
    _cjxl_path = None  # Cache the path to cjxl binary

    @classmethod
    def _get_cjxl_path(class_reference) -> Optional[Path]:
        if class_reference._cjxl_path is not None:
            return class_reference._cjxl_path

        # Determine platform-specific binary
        if sys.platform == 'win32':
            binary_name = 'cjxl.exe'
            rel_path = Path('libjxl-binaries/windows') / binary_name
        else:
            binary_name = 'cjxl'
            rel_path = Path('libjxl-binaries/linux') / binary_name

        binary_path = Path(__file__).parent.parent / rel_path

        if binary_path.exists():
            class_reference._cjxl_path = binary_path
            return binary_path

        try:
            result = subprocess.run([binary_name, '--version'],
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                class_reference._cjxl_path = Path(binary_name)
                return Path(binary_name)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    @staticmethod
    def convert_to_jxl(
        input_path: Path,
        output_path: Optional[Path] = None,
        remove_original: bool = True
    ) -> Path:
        if output_path is None:
            output_path = input_path.with_suffix('.jxl')

        # Get cjxl binary path
        cjxl_path = JXLConverter._get_cjxl_path()
        if cjxl_path is None:
            logger.debug("cjxl binary not found; skipping conversion for %s", input_path)
            return input_path

        try:
            command = [
                str(cjxl_path),
                '--lossless_jpeg=1',
                '--effort=9',
                str(input_path),
                str(output_path)
            ]

            result = subprocess.run(command, capture_output=True, timeout=120)

            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
                logger.warning("cjxl failed (%s) for %s: %s", result.returncode, input_path, stderr.strip())
                return input_path

            if remove_original and input_path != output_path:
                input_path.unlink(missing_ok=True)

            return output_path

        except Exception as exception:
            logger.warning("cjxl exception for %s: %s", input_path, exception)
            return input_path

    @staticmethod
    def is_convertible_image(file_path: Path) -> bool:
        if not file_path.exists():
            return False

        if file_path.suffix.lower() not in ('.jpg', '.jpeg'):
            return False

        try:
            with Image.open(file_path) as image:
                return image.format == 'JPEG'
        except Exception:
            return False
