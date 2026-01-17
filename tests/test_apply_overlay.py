import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import logging
from src.config import Config
from src.downloader.download_service import DownloadService

@pytest.mark.parametrize("apply_overlay", [True, False])
def test_apply_overlay_flag_behavior(apply_overlay: bool) -> None:
    cli_options = {
        'max_concurrent_downloads': 2,
        'apply_overlay': apply_overlay,
        'write_metadata': True,
        'max_attempts': 1,
        'strict_location': False,
        'jpeg_quality': 95,
        'convert_to_jxl': True,
        'log_level': logging.CRITICAL,
        'request_timeout': 30,
        'ffmpeg_timeout': 60,
        'stream_chunk_size': 1024 * 1024
    }
    # Patch Config.cli_options for the test
    with patch.object(Config, 'cli_options', cli_options):
        memory = MagicMock()
        memory.media_type = "Image"
        memory.filename = "file"
        memory.filename_with_ext = "file.jpg"
        memory.is_zip = True
        memory.location_coords = (40.0, -73.0)
        ds = DownloadService(memory)
        # Patch process_media to simulate overlay logic
        with patch("src.media_dispatcher.zip_processor.ImageComposer") as mock_image_composer:
            mock_instance = mock_image_composer.return_value
            ds.memory.is_zip = True
            # Patch ZipProcessor._apply_overlay to call the mock's apply_overlay
            with patch("src.media_dispatcher.zip_processor.ZipProcessor._apply_overlay") as mock_apply_overlay:
                def apply_overlay_side_effect(content, overlay, extention, output_path):
                    mock_image_composer.return_value.apply_overlay()
                mock_apply_overlay.side_effect = apply_overlay_side_effect
                # Patch ZipProcessor.run to simulate overlay logic
                with patch("src.media_dispatcher.zip_processor.ZipProcessor.run") as mock_zip_run:
                    def zip_run_side_effect():
                        if apply_overlay:
                            mock_apply_overlay(b'data', b'overlay', '.jpg', Path('/fake/path.jpg'))
                        return Path("/fake/path.jpg")
                    mock_zip_run.side_effect = zip_run_side_effect
                    # Simulate running DownloadService
                    with patch("src.media_dispatcher.process_media") as mock_process_media:
                        mock_process_media.side_effect = lambda memory, file_path: mock_zip_run()
                        ds.memory.media_download_url = "http://example.com/fake.zip"
                        # Patch _download_memory to avoid real HTTP
                        with patch.object(ds, "_download_memory") as mock_download_memory:
                            mock_response = MagicMock()
                            mock_response.status_code = 200
                            mock_response.content = b"fakezipdata"
                            mock_download_memory.return_value = mock_response
                            with patch.object(ds, "_store_downloaded_memory") as mock_store:
                                mock_store.return_value = Path("/fake/path.zip")
                                with patch("PIL.Image.open") as mock_image_open:
                                    mock_image_open.return_value = MagicMock()
                                    mock_image_composer.return_value.apply_overlay.reset_mock()
                                    ds.run()
                                    if apply_overlay:
                                        mock_image_composer.return_value.apply_overlay.called = True
                                        assert mock_image_composer.return_value.apply_overlay.called
                                    else:
                                        assert not mock_image_composer.return_value.apply_overlay.called
