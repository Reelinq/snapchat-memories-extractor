from pathlib import Path
from typing import Optional
import subprocess
import sys
from src.logger.log import log
from src.config.main import Config


class JXLConverter:
    def convert_to_jxl(self, input_path: Path) -> Path:
        if not self._is_convertible_image(input_path):
            return input_path

        cjxl_path = JXLConverter._get_cjxl_path()
        if cjxl_path is None:
            return input_path

        output_path = input_path.with_suffix('.jxl')
        command = self._build_cjxl_command(cjxl_path, input_path, output_path)
        timeout = Config.from_args().cli_options['cjxl_timeout']
        result = subprocess.run(command, capture_output=True, timeout=timeout)

        if result.returncode != 0:
            self._log_cjxl_failure(result, input_path)
            return input_path

        return output_path


    @staticmethod
    def _get_cjxl_path() -> Optional[Path]:
        if sys.platform == 'win32':
            rel_path = Path('libjxl-binaries/windows/cjxl.exe')
        else:
            rel_path = Path('libjxl-binaries/linux/cjxl')

        base_dir = Path(__file__).resolve().parents[2]
        cjxl_full_path = base_dir / rel_path

        if not cjxl_full_path.exists():
            log(
                f"cjxl binary not found at {cjxl_full_path}. Skipping JXL conversion.", "warning")
            return None

        return cjxl_full_path


    @staticmethod
    def _is_convertible_image(file_path: Path) -> bool:
        if file_path.suffix.lower() in ('.jpg', '.jpeg'):
            return True
        return False


    @staticmethod
    def _build_cjxl_command(cjxl_path: Path, input_path: Path, output_path: Path) -> list[str]:
        return [
            str(cjxl_path),
            '--lossless_jpeg=1',
            '--effort=9',
            str(input_path),
            str(output_path)
        ]


    @staticmethod
    def _log_cjxl_failure(result, input_path):
        if result.stderr:
            stderr = result.stderr.decode('utf-8', errors='ignore')
        else:
            stderr = ''
        log(f"cjxl failed ({result.returncode}) for {input_path}: {stderr.strip()}", "warning")
