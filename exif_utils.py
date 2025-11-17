from pathlib import Path
import piexif
import re
from datetime import datetime
from PIL import Image
from models import Memory

def add_exif_data(image_path: Path, memory: Memory):
    try:
        img = Image.open(image_path)

        try:
            exif_dict = piexif.load(str(image_path))
        except:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Format datetime for EXIF (YYYY:MM:DD HH:MM:SS)
        try:
            dt = datetime.strptime(memory.date, "%Y-%m-%d %H:%M:%S UTC")
            dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")

            # Set datetime fields in EXIF IFD
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = dt_str.encode('utf-8')
            exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = dt_str.encode('utf-8')
            exif_dict["0th"][piexif.ImageIFD.DateTime] = dt_str.encode('utf-8')
        except ValueError:
            pass

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

    except Exception as e:
        pass
