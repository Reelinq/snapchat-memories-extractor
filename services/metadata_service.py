from models import Memory
from pathlib import Path
import subprocess
import piexif
from PIL import Image
import imageio_ffmpeg

class MetadataService:
	# Cache ffmpeg path to avoid repeated lookups
	_ffmpeg_exe_cache = None

	@classmethod
	def _get_ffmpeg_exe(class_reference) -> str:
		if class_reference._ffmpeg_exe_cache is None:
			class_reference._ffmpeg_exe_cache = imageio_ffmpeg.get_ffmpeg_exe()
		return class_reference._ffmpeg_exe_cache

	def write_metadata(self, memory: Memory, file_path: Path, is_image: bool, ffmpeg_timeout: int = 60, jpeg_quality: int = 95):
		if is_image:
			self._write_image_metadata(memory, file_path, jpeg_quality)
		else:
			self._write_video_metadata(memory, file_path, ffmpeg_timeout)

	def _write_image_metadata(self, memory: Memory, file_path: Path, jpeg_quality: int = 95) -> None:
		with Image.open(file_path) as image:
			exif_data_dictionary = {"0th": {}, "Exif": {}, "GPS": {}}

			# Write datetime
			exif_data_dictionary["Exif"][piexif.ExifIFD.DateTimeOriginal] = memory.exif_datetime.encode('utf-8')
			exif_data_dictionary["Exif"][piexif.ExifIFD.DateTimeDigitized] = memory.exif_datetime.encode('utf-8')
			exif_data_dictionary["0th"][piexif.ImageIFD.DateTime] = memory.exif_datetime.encode('utf-8')

			# Write GPS if available
			coordinates = memory.location_coords
			if coordinates:
				latitude, longitude = coordinates
				latitude_degrees_minutes_seconds = self._decimal_to_dms(latitude)
				longitude_degrees_minutes_seconds = self._decimal_to_dms(longitude)

				exif_data_dictionary["GPS"][piexif.GPSIFD.GPSLatitude] = latitude_degrees_minutes_seconds
				exif_data_dictionary["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b'N' if latitude >= 0 else b'S'
				exif_data_dictionary["GPS"][piexif.GPSIFD.GPSLongitude] = longitude_degrees_minutes_seconds
				exif_data_dictionary["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b'E' if longitude >= 0 else b'W'

			exif_data_bytes = piexif.dump(exif_data_dictionary)
			image.save(str(file_path), exif=exif_data_bytes, quality=jpeg_quality)

	def _write_video_metadata(self, memory: Memory, file_path: Path, ffmpeg_timeout: int) -> None:
		ffmpeg_exe = self._get_ffmpeg_exe()
		metadata_args = ['-metadata', f'creation_time={memory.video_creation_time}']

		# Add GPS metadata if available
		coordinates = memory.location_coords
		if coordinates:
			latitude, longitude = coordinates
			latitude_sign = '+' if latitude >= 0 else ''
			longitude_sign = '+' if longitude >= 0 else ''
			iso6709_location_string = f"{latitude_sign}{latitude:.6f}{longitude_sign}{longitude:.6f}/"

			metadata_arguments.extend([
				'-metadata', f'location={iso6709_location_string}',
				'-metadata', f'com.apple.quicktime.location.ISO6709={iso6709_location_string}',
				'-metadata', f'Keys:GPSCoordinates={latitude}, {longitude}',
			])

		# Run ffmpeg
		temporary_video_path = file_path.with_suffix('.tmp.mp4')
		try:
			command = [
				ffmpeg_exe,
				'-i', str(file_path),
				'-c', 'copy',
				*metadata_args,
				'-y',
				str(temporary_video_path)
			]

			subprocess_execution_result = subprocess.run(
				command,
				stdout=subprocess.DEVNULL,
				stderr=subprocess.DEVNULL,
				timeout=ffmpeg_timeout
			)

			if subprocess_execution_result.returncode == 0:
				temporary_video_path.replace(file_path)
			else:
				if temporary_video_path.exists():
					temporary_video_path.unlink()
				raise Exception(f"ffmpeg failed with code {subprocess_execution_result.returncode}")
		except Exception:
			if temporary_video_path.exists():
				temporary_video_path.unlink()
			raise

	@staticmethod
	def _decimal_to_dms(decimal: float) -> tuple:
		degrees = int(abs(decimal))
		minutes_decimal = (abs(decimal) - degrees) * 60
		minutes = int(minutes_decimal)
		seconds = (minutes_decimal - minutes) * 60

		return (
			(degrees, 1),
			(minutes, 1),
			(int(seconds * 1000000), 1000000)
		)
