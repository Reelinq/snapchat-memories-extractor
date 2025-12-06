from zip_processor import ZipProcessor
from filename_resolver import FileNameResolver
from models import Memory
from config import Config
from services.metadata_service import MetadataService
from services.overlay_service import OverlayService
from services.media_processor import get_media_processor
from typing import List, Dict
import requests
import threading
from requests.adapters import HTTPAdapter

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
		from services.overlay_service import OverlayService
		OverlayService.shutdown_process_pool()

	def download_and_process(self, memory: Memory) -> bool:
		try:
			# Stream downloads for efficient memory usage
			response = self.session.get(
				memory.media_download_url,
				timeout=self.config.request_timeout,
				stream=True
			)
			if response.status_code >= 400:
				with self.stats_lock:
					self.errors.append({
						'filename': memory.filename_with_ext,
						'url': memory.media_download_url,
						'code': str(response.status_code)
					})
				return False
			response.raise_for_status()

			# Stream content in chunks to avoid RAM spikes
			content = b''
			for chunk in response.iter_content(chunk_size=self.config.stream_chunk_size):
				if chunk:
					content += chunk

			is_zip = self.content_processor.is_zip(
				content,
				response.headers.get('Content-Type', '')
			)
			if is_zip:
				return self._process_zip(content, memory)
			else:
				return self._process_regular(content, memory)
		except requests.exceptions.RequestException as e:
			with self.stats_lock:
				self.errors.append({
					'filename': memory.filename_with_ext,
					'url': memory.media_download_url,
					'code': 'NET'
				})
			return False
		except Exception as e:
			with self.stats_lock:
				self.errors.append({
					'filename': memory.filename_with_ext,
					'url': memory.media_download_url,
					'code': 'ERR'
				})
			return False

	def _process_zip(self, content: bytes, memory: Memory) -> bool:
		filepath = None
		try:
			media_bytes, extension, overlay_png = self.content_processor.extract_media_from_zip(
				content,
				extract_overlay=self.config.apply_overlay
			)

			processor = get_media_processor(
				memory.media_type,
				self.overlay_service,
				self.metadata_service
			)

			if filepath is None:
				filepath = self.config.downloads_folder / f"{memory.filename}{extension}"
				filepath = self.filename_resolver.resolve_unique_path(filepath)

			if self.config.apply_overlay and overlay_png:
				media_bytes = processor.apply_overlay(
					media_bytes,
					overlay_png,
					filepath,
					self.config.ffmpeg_timeout,
					self.config.jpeg_quality
				)

			if filepath is None or not filepath.exists():
				filepath.write_bytes(media_bytes)

			if self.config.write_metadata:
				processor.write_metadata(memory, filepath, self.config.ffmpeg_timeout, self.config.jpeg_quality)

			with self.stats_lock:
				self.total_bytes += filepath.stat().st_size
			return True
		except Exception as e:
			if filepath:
				filepath.unlink(missing_ok=True)
			with self.stats_lock:
				self.errors.append({
					'filename': memory.filename_with_ext,
					'url': memory.media_download_url,
					'code': 'ZIP'
				})
			return False

	def _process_regular(self, content: bytes, memory: Memory) -> bool:
		filepath = self.config.downloads_folder / memory.filename_with_ext
		filepath = self.filename_resolver.resolve_unique_path(filepath)
		try:
			filepath.write_bytes(content)
			if self.config.write_metadata:
				processor = get_media_processor(
					memory.media_type,
					self.overlay_service,
					self.metadata_service
				)
				processor.write_metadata(memory, filepath, self.config.ffmpeg_timeout, self.config.jpeg_quality)
			with self.stats_lock:
				self.total_bytes += filepath.stat().st_size
			return True
		except Exception as e:
			filepath.unlink(missing_ok=True)
			with self.stats_lock:
				self.errors.append({
					'filename': memory.filename_with_ext,
					'url': memory.media_download_url,
					'code': 'FILE'
				})
			return False
