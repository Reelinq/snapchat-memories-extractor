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
	def _get_ffmpeg_exe(cls) -> str:
		if cls._ffmpeg_exe_cache is None:
			cls._ffmpeg_exe_cache = imageio_ffmpeg.get_ffmpeg_exe()
		return cls._ffmpeg_exe_cache

	def write_metadata(self, memory: Memory, file_path: Path, is_image: bool, ffmpeg_timeout: int = 60):
		if is_image:
			self._write_image_metadata(memory, file_path)
		else:
			self._write_video_metadata(memory, file_path, ffmpeg_timeout)

	def _write_image_metadata(self, memory: Memory, file_path: Path) -> None:
		with Image.open(file_path) as img:
			exif_dict = {"0th": {}, "Exif": {}, "GPS": {}}

			# Write datetime
			exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = memory.exif_datetime.encode('utf-8')
			exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = memory.exif_datetime.encode('utf-8')
			exif_dict["0th"][piexif.ImageIFD.DateTime] = memory.exif_datetime.encode('utf-8')

			# Write GPS if available
			coords = memory.location_coords
			if coords:
				latitude, longitude = coords
				lat_dms = self._decimal_to_dms(latitude)
				lon_dms = self._decimal_to_dms(longitude)

				exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_dms
				exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b'N' if latitude >= 0 else b'S'
				exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lon_dms
				exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b'E' if longitude >= 0 else b'W'

			exif_bytes = piexif.dump(exif_dict)
			img.save(str(file_path), exif=exif_bytes, quality=95)

	def _write_video_metadata(self, memory: Memory, file_path: Path, ffmpeg_timeout: int) -> None:
		ffmpeg_exe = self._get_ffmpeg_exe()
		metadata_args = ['-metadata', f'creation_time={memory.video_creation_time}']

		# Add GPS metadata if available
		coords = memory.location_coords
		if coords:
			latitude, longitude = coords
			lat_sign = '+' if latitude >= 0 else ''
			lon_sign = '+' if longitude >= 0 else ''
			iso6709 = f"{lat_sign}{latitude:.6f}{lon_sign}{longitude:.6f}/"

			metadata_args.extend([
				'-metadata', f'location={iso6709}',
				'-metadata', f'com.apple.quicktime.location.ISO6709={iso6709}',
				'-metadata', f'Keys:GPSCoordinates={latitude}, {longitude}',
			])

		# Run ffmpeg
		temp_path = file_path.with_suffix('.tmp.mp4')
		try:
			cmd = [
				ffmpeg_exe,
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
				timeout=ffmpeg_timeout
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
