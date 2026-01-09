import tempfile
from pathlib import Path

import pytest

from src.filename_resolver import FileNameResolver


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def resolver(temp_dir):
    """Create a FileNameResolver instance"""
    return FileNameResolver(temp_dir)


def test_unique_filename_first_duplicate(temp_dir, resolver):
    """Test that first duplicate gets _1 suffix"""
    # Create the original file
    original = temp_dir / "file.txt"
    original.write_text("a")

    # Request a unique path for a file that already exists
    new_path = resolver.resolve_unique_path(original)

    # Debug: print what we got
    print(f"Original: {original}")
    print(f"Original exists: {original.exists()}")
    print(f"New path: {new_path}")
    print(f"New path exists: {new_path.exists()}")

    # The resolver should return file_1.txt since file.txt exists
    assert new_path.name == "file_1.txt"

    # Actually write the file
    new_path.write_text("b")


def test_unique_filename_second_duplicate(temp_dir, resolver):
    """Test that second duplicate gets _2 suffix"""
    # Create original
    original = temp_dir / "file.txt"
    original.write_text("a")

    # Get first duplicate path and create it
    first_dup = resolver.resolve_unique_path(original)
    first_dup.write_text("b")

    # Get second duplicate path
    second_dup = resolver.resolve_unique_path(original)

    assert first_dup.name == "file_1.txt"
    assert second_dup.name == "file_2.txt"
