from pathlib import Path
import subprocess
import piexif
from PIL import Image
import imageio_ffmpeg
from models import Memory

class ImageMetadataWriter:
    def __init__(self, memory: Memory):
        self.memory = memory

    def write_metadata(self, file_path: Path) -> None:
        with Image.open(file_path) as img:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}}

            self._write_datetime(exif_dict)

            location_coords = self.memory.location.replace('Latitude, Longitude: ', '')
            latitude, longitude = map(float, location_coords.split(', '))
            if not (latitude == 0.0 and longitude == 0.0):
                self._write_gps(exif_dict, latitude, longitude)

            exif_bytes = piexif.dump(exif_dict)
            img.save(str(file_path), exif=exif_bytes, quality=95)


    def _write_datetime(self, exif_dict: dict) -> None:
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = self.memory.exif_datetime.encode('utf-8')
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = self.memory.exif_datetime.encode('utf-8')
        exif_dict["0th"][piexif.ImageIFD.DateTime] = self.memory.exif_datetime.encode('utf-8')


    def _write_gps(self, exif_dict: dict, latitude: float, longitude: float) -> None:
        lat_dms = self._decimal_to_dms(latitude)
        lon_dms = self._decimal_to_dms(longitude)

        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_dms
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b'N' if latitude >= 0 else b'S'
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lon_dms
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b'E' if longitude >= 0 else b'W'


    @staticmethod
    def _decimal_to_dms(decimal: float) -> tuple:
        degrees = int(abs(decimal))
        minutes_decimal = (abs(decimal) - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60

        return (
            (degrees, 1),
            (minutes, 1),
            (int(seconds * 100), 100)
        )



class VideoMetadataWriter:
    def __init__(self, memory: Memory, ffmpeg_timeout: int = 60):
        self.memory = memory
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.timeout = ffmpeg_timeout


    def write_metadata(self, file_path: Path) -> None:
        metadata_args = self._write_datetime()

        location_coords = self.memory.location.replace('Latitude, Longitude: ', '')
        latitude, longitude = map(float, location_coords.split(', '))
        if not (latitude == 0.0 and longitude == 0.0):
            metadata_args.extend(self._write_gps(latitude, longitude))

        # Run ffmpeg
        temp_path = file_path.with_suffix('.tmp.mp4')
        try:
            cmd = [
                self.ffmpeg_exe,
                '-i', str(file_path),
                '-c', 'copy',
                *metadata_args,
                '-y',
                str(temp_path)
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.timeout
            )

            if result.returncode == 0:
                temp_path.replace(file_path)
            else:
                if temp_path.exists():
                    temp_path.unlink()
                raise Exception(f"ffmpeg failed with code {result.returncode}")
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise


    def _write_datetime(self) -> list[str]:
        return ['-metadata', f'creation_time={self.memory.video_creation_time}']


    @staticmethod
    def _write_gps(latitude: float, longitude: float) -> list[str]:
        lat_sign = '+' if latitude >= 0 else ''
        lon_sign = '+' if longitude >= 0 else ''
        iso6709 = f"{lat_sign}{latitude:.6f}{lon_sign}{longitude:.6f}/"

        return [
            '-metadata', f'location={iso6709}',
            '-metadata', f'com.apple.quicktime.location.ISO6709={iso6709}',
            '-metadata', f'Keys:GPSCoordinates={latitude}, {longitude}',
        ]
