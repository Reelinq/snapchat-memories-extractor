from pathlib import Path
from typing import Optional
import subprocess
import sys
from src.logger import log
from src.config import Config


class JXLConverter:
    def __init__(self, input_path: Path):
        self.input_path = input_path


    def run(self) -> Path:
        if not self._is_convertible_image():
            return self.input_path

        cjxl_path = JXLConverter._get_cjxl_path()
        if cjxl_path is None:
            return self.input_path

        output_path = self.input_path.with_suffix('.jxl')
        command = self._build_cjxl_command(cjxl_path, output_path)
        timeout = Config.cli_options['cjxl_timeout']
        result = subprocess.run(command, capture_output=True, timeout=timeout)

        if result.returncode != 0:
            self._log_cjxl_failure(result)
            return self.input_path

        if output_path.exists() and self.input_path.exists():
            self.input_path.unlink()

        if output_path.exists() and self.input_path.exists():
            self.input_path.unlink()
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


    def _is_convertible_image(self) -> bool:
        if self.input_path.suffix.lower() in ('.jpg', '.jpeg') and self.input_path.exists():
            return True
        return False


    def _build_cjxl_command(self, cjxl_path: Path, output_path: Path) -> list[str]:
        return [
            str(cjxl_path),
            '--lossless_jpeg=1',
            '--effort=9',
            str(self.input_path),
            str(output_path)
        ]


    def _log_cjxl_failure(self, result: subprocess.CompletedProcess) -> None:
        if result.stderr:
            stderr = result.stderr.decode('utf-8', errors='ignore')
        else:
            stderr = ''
        log(f"cjxl failed ({result.returncode}) for {self.input_path}: {stderr.strip()}", "warning")
