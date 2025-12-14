import unittest
from src.models import *

class TestModels(unittest.TestCase):
    def test_memory_creation_and_properties(self):
        data = {
            "Date": "2023-12-05 12:34:56 UTC",
            "Media Download Url": "http://example.com/media.jpg",
            "Media Type": "Image",
            "Location": "Latitude, Longitude: 37.7749, -122.4194"
        }
        m = Memory(**data)
        self.assertEqual(m.exif_datetime, "2023:12:05 12:34:56")
        self.assertEqual(m.video_creation_time, "2023-12-05T12:34:56")
        self.assertEqual(m.filename, "2023-12-05_12-34-56")
        self.assertEqual(m.extension, ".jpg")
        self.assertEqual(m.filename_with_ext, "2023-12-05_12-34-56.jpg")
        self.assertEqual(m.location_coords, (37.7749, -122.4194))

    def test_memory_no_location(self):
        data = {
            "Date": "2023-12-05 12:34:56 UTC",
            "Media Download Url": "http://example.com/media.mp4",
            "Media Type": "Video",
            "Location": "Latitude, Longitude: 0.0, 0.0"
        }
        m = Memory(**data)
        self.assertIsNone(m.location_coords)
        self.assertEqual(m.extension, ".mp4")

    def test_memory_missing_location(self):
        data = {
            "Date": "2023-12-05 12:34:56 UTC",
            "Media Download Url": "http://example.com/media.mp4",
            "Media Type": "Video",
            "Location": None
        }
        m = Memory(**data)
        self.assertIsNone(m.location_coords)

if __name__ == "__main__":
    unittest.main()
