import piexif
from pathlib import Path
from PIL import Image
from src.memory_model import Memory
from src.config.main import Config


class ImageMetadataWriter:
    def __init__(self):
        self.exif_metadata = {"0th": {}, "Exif": {}, "GPS": {}}


    def write_image_metadata(self, memory: Memory, file_path: Path):
        self._set_datetime_fields(memory.exif_datetime)
        self._set_gps_fields(memory.location_coords)
        self._save_image_with_exif(file_path, self.exif_metadata)


    def _set_datetime_fields(self, exif_datetime):
        datetime_bytes = exif_datetime.encode('utf-8')
        exif = self.exif_metadata["Exif"]
        zeroth = self.exif_metadata["0th"]

        exif[piexif.ExifIFD.DateTimeOriginal] = datetime_bytes
        exif[piexif.ExifIFD.DateTimeDigitized] = datetime_bytes
        zeroth[piexif.ImageIFD.DateTime] = datetime_bytes


    def _set_gps_fields(self, coordinates):
        if not coordinates:
            return

        latitude, longitude = coordinates
        gps = self.exif_metadata["GPS"]
        latitude_dms = self._decimal_to_dms(latitude)
        longitude_dms = self._decimal_to_dms(longitude)

        lat_ref = b'N' if latitude >= 0 else b'S'
        lon_ref = b'E' if longitude >= 0 else b'W'

        gps[piexif.GPSIFD.GPSLatitude] = latitude_dms
        gps[piexif.GPSIFD.GPSLatitudeRef] = lat_ref
        gps[piexif.GPSIFD.GPSLongitude] = longitude_dms
        gps[piexif.GPSIFD.GPSLongitudeRef] = lon_ref


    @staticmethod
    def _decimal_to_dms(decimal_degrees: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        absolute_value = abs(decimal_degrees)

        degrees = int(absolute_value)
        degrees_fraction = absolute_value - degrees

        minutes_decimal = degrees_fraction * 60
        minutes = int(minutes_decimal)
        minutes_fraction = minutes_decimal - minutes

        seconds_decimal = minutes_fraction * 60
        seconds_numerator = int(seconds_decimal * 1000000)
        seconds_denominator = 1000000

        return (
            (degrees, 1),
            (minutes, 1),
            (seconds_numerator, seconds_denominator)
        )


    @staticmethod
    def _save_image_with_exif(file_path: Path, exif_metadata: dict) -> None:
        quality = Config.from_args().cli_options['jpeg_quality']
        exif_data_bytes = piexif.dump(exif_metadata)

        with Image.open(file_path) as image:
            image.save(str(file_path), exif=exif_data_bytes, quality=quality)
