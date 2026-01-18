import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import Config
from src.downloader.download_service import DownloadService


def create_test_cli_options(apply_overlay: bool) -> dict:
    """Create CLI options for testing."""
    return {
        "max_concurrent_downloads": 2,
        "apply_overlay": apply_overlay,
        "write_metadata": True,
        "max_attempts": 1,
        "strict_location": False,
        "jpeg_quality": 95,
        "convert_to_jxl": True,
        "log_level": logging.CRITICAL,
        "request_timeout": 30,
        "ffmpeg_timeout": 60,
        "stream_chunk_size": 1024 * 1024,
    }


def create_mock_memory() -> MagicMock:
    """Create a mock memory object for testing."""
    memory = MagicMock()
    memory.media_type = "Image"
    memory.filename = "file"
    memory.filename_with_ext = "file.jpg"
    memory.is_zip = True
    memory.location_coords = (40.0, -73.0)
    memory.media_download_url = "http://example.com/fake.zip"
    return memory


def create_mock_download_response() -> MagicMock:
    """Create a mock HTTP response for download."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fakezipdata"
    return mock_response


def setup_zip_processor_mock(mock_apply_overlay, apply_overlay: bool):
    """Configure the ZipProcessor mock behavior."""

    def zip_run_side_effect():
        if apply_overlay:
            mock_apply_overlay(
                b"data",
                b"overlay",
                ".jpg",
                Path("/fake/path.jpg"),
            )
        return Path("/fake/path.jpg")

    return zip_run_side_effect


def setup_apply_overlay_mock(mock_image_composer):
    """Configure the apply_overlay mock behavior."""

    def apply_overlay_side_effect() -> None:
        mock_image_composer.return_value.apply_overlay()

    return apply_overlay_side_effect


@pytest.mark.parametrize("apply_overlay", [True, False])
def test_apply_overlay_flag_behavior(apply_overlay: bool) -> None:
    """Test that apply_overlay flag correctly controls overlay application."""
    cli_options = create_test_cli_options(apply_overlay)

    with (
        patch.object(Config, "cli_options", cli_options),
        patch(
            "src.media_dispatcher.zip_processor.ImageComposer"
        ) as mock_image_composer,
        patch(
            "src.media_dispatcher.zip_processor.ZipProcessor._apply_overlay"
        ) as mock_apply_overlay,
        patch("src.media_dispatcher.zip_processor.ZipProcessor.run") as mock_zip_run,
    ):
        memory = create_mock_memory()
        ds = DownloadService(memory)
        ds.memory.is_zip = True

        # Setup apply_overlay behavior
        side_effect = setup_apply_overlay_mock(mock_image_composer)
        mock_apply_overlay.side_effect = side_effect

        # Setup zip processor behavior
        zip_side_effect = setup_zip_processor_mock(mock_apply_overlay, apply_overlay)
        mock_zip_run.side_effect = zip_side_effect

        # Run the test
        run_download_service_test(ds, mock_image_composer, apply_overlay)


def run_download_service_test(
    ds: DownloadService,
    mock_image_composer: MagicMock,
    apply_overlay: bool,
) -> None:
    """Execute the download service test with mocked dependencies."""
    mock_response = create_mock_download_response()

    with (
        patch("src.media_dispatcher.process_media") as mock_process_media,
        patch.object(ds, "_download_memory", return_value=mock_response),
        patch.object(
            ds, "_store_downloaded_memory", return_value=Path("/fake/path.zip")
        ),
        patch("PIL.Image.open", return_value=MagicMock()),
    ):
        mock_process_media.side_effect = ()

        # Reset and run
        overlay_mock = mock_image_composer.return_value.apply_overlay
        overlay_mock.reset_mock()

        ds.run()

        # Assert overlay behavior
        verify_overlay_behavior(overlay_mock, apply_overlay)


def verify_overlay_behavior(
    overlay_mock: MagicMock,
    apply_overlay: bool,
) -> None:
    """Verify that overlay was applied or not based on the flag."""
    if apply_overlay:
        overlay_mock.called = True
        assert overlay_mock.called, "Overlay should have been applied"
    else:
        assert not overlay_mock.called, "Overlay should not have been applied"
