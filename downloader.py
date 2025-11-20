import json
import time
from typing import List, Dict
import requests
from config import Config
from models import Memory
from filename_resolver import FileNameResolver
from zip_processor import ZipProcessor
from metadata_writers import ImageMetadataWriter, VideoMetadataWriter
from ui import print_status, update_progress, clear_lines, print_error_summary

class MemoryDownloader:
    def __init__(self, config: Config):
        self.config = config
        self.filename_resolver = FileNameResolver(config.downloads_folder)
        self.content_processor = ZipProcessor()

        # Statistics
        self.successful = 0
        self.failed = 0
        self.total_bytes = 0
        self.start_time = 0.0
        self.errors: List[Dict[str, str]] = []


    def run(self) -> None:
        data = self._load_json()
        raw_items = data.get('Saved Media', [])
        success_indices = set()
        total_files = len(raw_items)
        self.start_time = time.time()

        for index, item in enumerate(raw_items, 1):
            memory = Memory.model_validate(item)
            filename = memory.filename_with_ext

            update_progress(index, total_files, self.successful, self.failed, self.start_time, filename)

            try:
                if self._download_and_process(memory):
                    self.successful += 1
                    success_indices.add(index - 1)
                    self._prune_json(data, raw_items, success_indices)
                else:
                    self.failed += 1
            except Exception as e:
                self.failed += 1
                self.errors.append({
                    'filename': filename,
                    'url': memory.media_download_url,
                    'code': 'ERR'
                })

        self._prune_json(data, raw_items, success_indices)
        clear_lines(10)
        total_time = time.time() - self.start_time
        print_status(total_files, total_files, self.successful, self.failed, total_time, "✅ COMPLETE!")

        if self.errors:
            print_error_summary(self.errors)


    def _load_json(self) -> Dict:
        with open(self.config.json_path, 'r', encoding='utf-8') as file:
            return json.load(file)


    def _download_and_process(self, memory: Memory) -> bool:
        try:
            response = requests.get(memory.media_download_url, timeout=self.config.request_timeout)

            # Check status code and extract it before raising
            if response.status_code >= 400:
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
            self.errors.append({
                'filename': memory.filename_with_ext,
                'url': memory.media_download_url,
                'code': 'NET'
            })
            return False
        except Exception as e:
            self.errors.append({
                'filename': memory.filename_with_ext,
                'url': memory.media_download_url,
                'code': 'ERR'
            })
            return False


    def _process_zip(self, content: bytes, memory: Memory) -> bool:
        filepath = None
        try:
            media_bytes, extension = self.content_processor.extract_media_from_zip(content)

            filepath = self.config.downloads_folder / f"{memory.filename}{extension}"
            filepath = self.filename_resolver.resolve_unique_path(filepath)

            filepath.write_bytes(media_bytes)

            is_image = memory.media_type == "Image"
            writer = ImageMetadataWriter(memory) if is_image else VideoMetadataWriter(memory, self.config.ffmpeg_timeout)
            writer.write_metadata(filepath)

            self.total_bytes += filepath.stat().st_size
            return True

        except Exception as e:
            if filepath:
                filepath.unlink(missing_ok=True)
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

            is_image = memory.media_type == "Image"
            writer = ImageMetadataWriter(memory) if is_image else VideoMetadataWriter(memory, self.config.ffmpeg_timeout)
            writer.write_metadata(filepath)

            self.total_bytes += filepath.stat().st_size
            return True

        except Exception as e:
            filepath.unlink(missing_ok=True)
            self.errors.append({
                'filename': memory.filename_with_ext,
                'url': memory.media_download_url,
                'code': 'FILE'
            })
            return False


    def _prune_json(self, data: Dict, raw_items: List, success_indices: set) -> None:
        if not success_indices:
            return

        remaining = [itm for i, itm in enumerate(raw_items) if i not in success_indices]
        data['Saved Media'] = remaining

        with open(self.config.json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
