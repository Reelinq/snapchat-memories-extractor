import pytest
from src.memories.memory_model import Memory

@pytest.fixture
def image_memory_data():
    return {
        "Date": "2023-12-05 12:34:56 UTC",
        "Media Download Url": "http://example.com/media.jpg",
        "Media Type": "Image",
        "Location": "Latitude, Longitude: 37.7749, -122.4194"
    }

@pytest.fixture
def video_memory_data_no_location():
    return {
        "Date": "2023-12-05 12:34:56 UTC",
        "Media Download Url": "http://example.com/media.mp4",
        "Media Type": "Video",
        "Location": "Latitude, Longitude: 0.0, 0.0"
    }

@pytest.fixture
def video_memory_data_missing_location():
    return {
        "Date": "2023-12-05 12:34:56 UTC",
        "Media Download Url": "http://example.com/media.mp4",
        "Media Type": "Video",
        "Location": None
    }

def test_memory_creation_and_properties(image_memory_data):
    m = Memory.model_validate(image_memory_data)
    assert m.exif_datetime == "2023:12:05 12:34:56"
    assert m.video_creation_time == "2023-12-05T12:34:56"
    assert m.filename == "2023-12-05_12-34-56"
    assert m.extension == ".jpg"
    assert m.filename_with_ext == "2023-12-05_12-34-56.jpg"
    assert m.location_coords == (37.7749, -122.4194)

def test_memory_no_location(video_memory_data_no_location):
    m = Memory.model_validate(video_memory_data_no_location)
    assert m.location_coords is None
    assert m.extension == ".mp4"

def test_memory_missing_location(video_memory_data_missing_location):
    m = Memory.model_validate(video_memory_data_missing_location)
    assert m.location_coords is None
