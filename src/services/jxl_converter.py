from pathlib import Path
from PIL import Image
from typing import Optional
import subprocess
import sys
from src.logger.log import log
from src.error_handling import handle_errors

class JXLConverter:
    _cjxl_path = None

    @classmethod
    def _get_cjxl_path(class_reference) -> Optional[Path]:
        if class_reference._cjxl_path is not None:
            return class_reference._cjxl_path

        if sys.platform == 'win32':
            binary_name = 'cjxl.exe'
            rel_path = Path('libjxl-binaries/windows') / binary_name
        else:
            binary_name = 'cjxl'
            rel_path = Path('libjxl-binaries/linux') / binary_name

        base_dir = Path(__file__).resolve().parent.parent.parent
        binary_path = base_dir / rel_path

        if binary_path.exists():
            class_reference._cjxl_path = binary_path
            return binary_path

        if class_reference._check_system_binary(binary_name):
            class_reference._cjxl_path = Path(binary_name)
            return Path(binary_name)

        return None

    @classmethod
    @handle_errors(return_on_error=False)
    def _check_system_binary(class_reference, binary_name: str) -> bool:
        result = subprocess.run([binary_name, '--version'],
                                capture_output=True, timeout=5)
        return result.returncode == 0

    @staticmethod
    @handle_errors(return_on_error=None)
    def convert_to_jxl(
        input_path: Path,
        output_path: Optional[Path] = None,
        remove_original: bool = True
    ) -> Path:
        if output_path is None:
            output_path = input_path.with_suffix('.jxl')

        cjxl_path = JXLConverter._get_cjxl_path()
        if cjxl_path is None:
            log(
                f"cjxl binary not found; skipping conversion for {input_path}", level="debug")
            return input_path

        command = [
            str(cjxl_path),
            '--lossless_jpeg=1',
            '--effort=9',
            str(input_path),
            str(output_path)
        ]

        result = subprocess.run(command, capture_output=True, timeout=120)

        if result.returncode != 0:
            stderr = result.stderr.decode(
                'utf-8', errors='ignore') if result.stderr else ''
            log(f"cjxl failed ({result.returncode}) for {input_path}: {stderr.strip()}", level="warning")
            return input_path

        if remove_original and input_path != output_path:
            input_path.unlink(missing_ok=True)

        return output_path

    @staticmethod
    @handle_errors(return_on_error=False)
    def is_convertible_image(file_path: Path) -> bool:
        if not file_path.exists():
            return False

        if file_path.suffix.lower() not in ('.jpg', '.jpeg'):
            return False

        with Image.open(file_path) as image:
            return image.format == 'JPEG'
