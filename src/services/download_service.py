from src.services.zip_processor import ZipProcessor
from src.processors.filename_resolver import FileNameResolver
from src.models import Memory
from src.config.main import Config
from src.overlay.video_composer import VideoComposer
from src.media_dispatcher.media_dispatcher import process_media
from typing import List, Dict
from src.logger.log import log
import requests
import threading
from requests.adapters import HTTPAdapter
from src.overlay.video_composer import VideoComposer


class DownloadService:
    def __init__(self, stats_lock: threading.Lock):
        self.filename_resolver = FileNameResolver(Config.downloads_folder)
        self.content_processor = ZipProcessor()
        self.overlay_service = VideoComposer()
        self.stats_lock = stats_lock
        self.errors: List[Dict[str, str]] = []
        self.total_bytes = 0
        self.session = self._build_session()

    def download_and_process(self, memory: Memory):
        http_response = self.session.get(
            memory.media_download_url,
            timeout=self.config.cli_options['request_timeout'],
            stream=True
        )
        if http_response.status_code >= 400:
            log(f"Failed to download {memory.filename_with_ext}",
                "error", http_response.status_code)
            return None, False

        downloaded_file_content = b''
        for chunk in http_response.iter_content(chunk_size=self.config.cli_options['stream_chunk_size']):
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


    def _build_session(self) -> requests.Session:
        http_session = requests.Session()
        adapter = self._create_http_adapter()
        http_session.mount("https://", adapter)
        return http_session


    def _create_http_adapter():
        max_concurrent = Config.cli_options['max_concurrent_downloads']
        adapter = HTTPAdapter(
            pool_connections=max_concurrent,
            pool_maxsize=max_concurrent * 2,
        )
        return adapter


    def close(self) -> None:
        self.session.close()
        VideoComposer.shutdown_process_pool()


    def _process_zip(self, downloaded_file_content: bytes, memory: Memory):
        filepath = None
        media_bytes, extension, overlay_png = self.content_processor.extract_media_from_zip(
            downloaded_file_content,
            extract_overlay=self.config.cli_options['apply_overlay']
        )

        media_file_processor = process_media(
            memory.media_type,
            self.overlay_service,
            self.metadata_service,
            self.config.cli_options['convert_to_jxl']
        )

        if filepath is None:
            filepath = self.config.downloads_folder / \
                f"{memory.filename}{extension}"
            filepath = self.filename_resolver.resolve_unique_path(filepath)

        if filepath is None or not filepath.exists():
            filepath.write_bytes(media_bytes)

        with self.stats_lock:
            self.total_bytes += filepath.stat().st_size
        return filepath, True

    def _process_regular(self, downloaded_file_content: bytes, memory: Memory):
        filepath = self.config.downloads_folder / memory.filename_with_ext
        filepath = self.filename_resolver.resolve_unique_path(filepath)

        filepath.write_bytes(downloaded_file_content)
        with self.stats_lock:
            self.total_bytes += filepath.stat().st_size
        return filepath, True
