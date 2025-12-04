from zip_processor import ZipProcessor
from filename_resolver import FileNameResolver
from models import Memory
from config import Config
from services.metadata_service import MetadataService
from services.overlay_service import OverlayService
from typing import List, Dict
import requests
import threading

class DownloadService:
	def __init__(self, config: Config):
		self.config = config
		self.filename_resolver = FileNameResolver(config.downloads_folder)
		self.content_processor = ZipProcessor()
		self.metadata_service = MetadataService()
		self.overlay_service = OverlayService()
		self.stats_lock = threading.Lock()
		self.errors: List[Dict[str, str]] = []
		self.total_bytes = 0

	def download_and_process(self, memory: Memory) -> bool:
		try:
			response = requests.get(memory.media_download_url, timeout=self.config.request_timeout)
			if response.status_code >= 400:
				with self.stats_lock:
					self.errors.append({
						'filename': memory.filename_with_ext,
						'url': memory.media_download_url,
						'code': str(response.status_code)
					})
				return False
			response.raise_for_status()
			is_zip = self.content_processor.is_zip(
				response.content,
				response.headers.get('Content-Type', '')
			)
			if is_zip:
				return self._process_zip(response.content, memory)
			else:
				return self._process_regular(response.content, memory)
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
			if self.config.apply_overlay and overlay_png:
				is_image = memory.media_type == "Image"
				if is_image:
					media_bytes = self.overlay_service.apply_overlay_to_image(media_bytes, overlay_png)
				else:
					filepath = self.config.downloads_folder / f"{memory.filename}{extension}"
					filepath = self.filename_resolver.resolve_unique_path(filepath)
					self.overlay_service.apply_overlay_to_video(
						media_bytes,
						overlay_png,
						filepath,
						self.config.ffmpeg_timeout
					)
			if filepath is None:
				filepath = self.config.downloads_folder / f"{memory.filename}{extension}"
				filepath = self.filename_resolver.resolve_unique_path(filepath)
				filepath.write_bytes(media_bytes)
			if self.config.write_metadata:
				is_image = memory.media_type == "Image"
				self.metadata_service.write_metadata(memory, filepath, is_image, self.config.ffmpeg_timeout)
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
				is_image = memory.media_type == "Image"
				self.metadata_service.write_metadata(memory, filepath, is_image, self.config.ffmpeg_timeout)
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