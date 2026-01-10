import subprocess
from src.models import Memory
from pathlib import Path
import imageio_ffmpeg
from src.config.main import Config
from src.logger.log import log


class VideoMetadataWriter:
    def write_video_metadata(self, memory: Memory, file_path: Path):
        temporary_video_path = file_path.with_suffix('.tmp.mp4')
        command = self._build_ffmpeg_command(file_path, memory, temporary_video_path)

        timeout = Config.from_args().cli_options['ffmpeg_timeout']
        ffmpeg_run_result = subprocess.run(command, capture_output=True, timeout=timeout)

        if ffmpeg_run_result.returncode == 0:
            temporary_video_path.replace(file_path)
        else:
            self._log_ffmpeg_failure(ffmpeg_run_result, file_path, temporary_video_path)

        return file_path


    def _build_ffmpeg_command(self, file_path: Path, memory: Memory, temporary_video_path: Path) -> list[str]:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        metadata_arguments = self._ffmpeg_metadata_arguments(memory)

        command = [
            ffmpeg_exe,
            '-i', str(file_path),
            '-c', 'copy',
            *metadata_arguments,
            str(temporary_video_path)
        ]

        return command


    def _ffmpeg_metadata_arguments(self, memory) -> list[str]:
        meta_args = ['-metadata', f'creation_time={memory.video_creation_time}']

        if memory.location_coords:
            latitude, longitude = memory.location_coords
            iso6709 = self._to_iso6709(latitude, longitude)
            self._extend_meta_args(meta_args, latitude, longitude, iso6709)

        return meta_args


    @staticmethod
    def _to_iso6709(lat: float, lon: float) -> str:
        lat_sign = '+' if lat >= 0 else ''
        lon_sign = '+' if lon >= 0 else ''
        return f"{lat_sign}{lat:.6f}{lon_sign}{lon:.6f}/"


    @staticmethod
    def _extend_meta_args(args: list[str], lat: float, lon: float, iso6709: str) -> None:
        args.extend([
            '-metadata', f'location={iso6709}',
            '-metadata', f'com.apple.quicktime.location.ISO6709={iso6709}',
            '-metadata', f'Keys:GPSCoordinates={lat}, {lon}',
        ])


    @staticmethod
    def _log_ffmpeg_failure(result, file_path, temp_path):
        if temp_path.exists():
            temp_path.unlink()
        log(f"ffmpeg failed with code {result.returncode} for {file_path}", "warning")
