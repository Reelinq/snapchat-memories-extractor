from src.processors.zip_processor import ZipProcessor
from src.processors.filename_resolver import FileNameResolver
from src.models import Memory
from src.config import Config
from src.services.metadata_service import MetadataService
from src.services.overlay_service import OverlayService
from src.services.media_processor import get_media_processor
from src.services.jxl_converter import JXLConverter
from typing import List, Dict
import requests
import threading
from requests.adapters import HTTPAdapter
from src.error_handling import handle_errors


class DownloadService:
    def __init__(self, config: Config, stats_lock: threading.Lock):
        self.config = config
        self.filename_resolver = FileNameResolver(config.downloads_folder)
        self.content_processor = ZipProcessor()
        self.metadata_service = MetadataService()
        self.overlay_service = OverlayService()
        self.stats_lock = stats_lock
        self.errors: List[Dict[str, str]] = []
        self.total_bytes = 0
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=self.config.max_concurrent_downloads,
            pool_maxsize=self.config.max_concurrent_downloads * 2,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def close(self) -> None:
        self.session.close()
        from src.services.overlay_service import OverlayService
        OverlayService.shutdown_process_pool()

    @handle_errors(return_on_error=False)
    def download_and_process(self, memory: Memory) -> bool:
        http_response = self.session.get(
            memory.media_download_url,
            timeout=self.config.request_timeout,
            stream=True
        )
        http_response.raise_for_status()  # Decorator catches HTTPError

        downloaded_file_content = b''
        for chunk in http_response.iter_content(chunk_size=self.config.stream_chunk_size):
            if chunk:
                downloaded_file_content += chunk

        is_zip_file = self.content_processor.is_zip(
            downloaded_file_content,
            http_response.headers.get('Content-Type', '')
        )
        if is_zip_file:
            return self._process_zip(downloaded_file_content, memory)
        else:
            return self._process_regular(downloaded_file_content, memory)

    @handle_errors(return_on_error=False)
    def _process_zip(self, downloaded_file_content: bytes, memory: Memory) -> bool:
        filepath = None
        media_bytes, extension, overlay_png = self.content_processor.extract_media_from_zip(
            downloaded_file_content,
            extract_overlay=self.config.apply_overlay
        )

        media_file_processor = get_media_processor(
            memory.media_type,
            self.overlay_service,
            self.metadata_service,
            self.config.convert_to_jxl
        )

        if filepath is None:
            filepath = self.config.downloads_folder / \
                f"{memory.filename}{extension}"
            filepath = self.filename_resolver.resolve_unique_path(filepath)

        if self.config.apply_overlay and overlay_png:
            media_bytes = media_file_processor.apply_overlay(
                media_bytes,
                overlay_png,
                filepath,
                self.config.ffmpeg_timeout,
                self.config.jpeg_quality
            )

        if filepath is None or not filepath.exists():
            filepath.write_bytes(media_bytes)

        if self.config.write_metadata:
            filepath = media_file_processor.write_metadata(
                memory, filepath, self.config.ffmpeg_timeout, self.config.jpeg_quality)
        elif self.config.convert_to_jxl and memory.media_type == "Image" and JXLConverter.is_convertible_image(filepath):
            filepath = JXLConverter.convert_to_jxl(filepath)

        with self.stats_lock:
            self.total_bytes += filepath.stat().st_size
        return True

    @handle_errors(return_on_error=False)
    def _process_regular(self, downloaded_file_content: bytes, memory: Memory) -> bool:
        filepath = self.config.downloads_folder / memory.filename_with_ext
        filepath = self.filename_resolver.resolve_unique_path(filepath)

        filepath.write_bytes(downloaded_file_content)
        if self.config.write_metadata:
            media_file_processor = get_media_processor(
                memory.media_type,
                self.overlay_service,
                self.metadata_service,
                self.config.convert_to_jxl
            )
            filepath = media_file_processor.write_metadata(
                memory, filepath, self.config.ffmpeg_timeout, self.config.jpeg_quality)
        elif self.config.convert_to_jxl and memory.media_type == "Image" and JXLConverter.is_convertible_image(filepath):
            filepath = JXLConverter.convert_to_jxl(filepath)
        with self.stats_lock:
            self.total_bytes += filepath.stat().st_size
        return True
