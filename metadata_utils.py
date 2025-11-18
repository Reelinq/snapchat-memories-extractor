from pathlib import Path
import piexif
import re
import subprocess
from datetime import datetime
from PIL import Image
from models import Memory
import imageio_ffmpeg

# Get bundled ffmpeg from imageio-ffmpeg package
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

def add_image_data(image_path: Path, memory: Memory):
    img = Image.open(image_path)

    try:
        exif_dict = piexif.load(str(image_path))
    except:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    # Format datetime for EXIF (YYYY:MM:DD HH:MM:SS)
    dt = datetime.strptime(memory.date, "%Y-%m-%d %H:%M:%S UTC")
    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")

    # Set datetime fields in EXIF IFD
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = dt_str.encode('utf-8')
    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = dt_str.encode('utf-8')
    exif_dict["0th"][piexif.ImageIFD.DateTime] = dt_str.encode('utf-8')

    # Parse location string:
    if memory.location:
        m = re.search(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", memory.location)
        if m:
            try:
                latitude = float(m.group(1))
                longitude = float(m.group(2))

                # Convert into DMS
                def decimal_to_dms(decimal):
                    degrees = int(abs(decimal))
                    minutes_decimal = (abs(decimal) - degrees) * 60
                    minutes = int(minutes_decimal)
                    seconds = (minutes_decimal - minutes) * 60

                    return (
                        (degrees, 1),
                        (minutes, 1),
                        (int(seconds * 100), 100)
                    )

                lat_dms = decimal_to_dms(latitude)
                lon_dms = decimal_to_dms(longitude)

                # Set GPS IFD fields
                exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_dms
                exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b'N' if latitude >= 0 else b'S'
                exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lon_dms
                exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b'E' if longitude >= 0 else b'W'
            except ValueError:
                pass

    # Convert back to bytes and save
    exif_bytes = piexif.dump(exif_dict)
    img.save(str(image_path), exif=exif_bytes, quality=95)


def add_video_metadata(video_path: Path, memory: Memory):
    # Parse date - raise exception if fails
    dt = datetime.strptime(memory.date, "%Y-%m-%d %H:%M:%S UTC")
    creation_time = dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Parse location if available
    latitude = None
    longitude = None
    if memory.location:
        m = re.search(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", memory.location)
        if m:
            try:
                latitude = float(m.group(1))
                longitude = float(m.group(2))
            except ValueError:
                pass

    # Use imageio-ffmpeg bundled binary to set creation time and GPS location
    temp_path = video_path.with_suffix('.tmp.mp4')
    try:
        # Build metadata args
        metadata_args = [
            '-metadata', f'creation_time={creation_time}',
        ]

        # Add GPS location metadata if available
        # Use multiple formats for maximum compatibility
        if latitude is not None and longitude is not None:
            # ISO 6709 format: +latitude+longitude/ (standard format)
            lat_sign = '+' if latitude >= 0 else ''
            lon_sign = '+' if longitude >= 0 else ''
            iso6709 = f"{lat_sign}{latitude:.6f}{lon_sign}{longitude:.6f}/"

            metadata_args.extend([
                '-metadata', f'location={iso6709}',
                '-metadata', f'com.apple.quicktime.location.ISO6709={iso6709}',
                '-metadata', f'Keys:GPSCoordinates={latitude}, {longitude}',
            ])

        cmd = [
            FFMPEG_EXE,
            '-i', str(video_path),
            '-c', 'copy',
            *metadata_args,
            '-y',
            str(temp_path)
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60
        )

        if result.returncode == 0:
            temp_path.replace(video_path)
        else:
            if temp_path.exists():
                temp_path.unlink()
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"Warning: Failed to write metadata to {video_path.name}: {e}")
