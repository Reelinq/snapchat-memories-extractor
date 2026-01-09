from src.filename_resolver import FileNameResolver
from src.models import Memory
from src.config.main import Config
from src.media_dispatcher.media_dispatcher import MediaDispatcher
from src.logger.log import log
import requests
from requests.adapters import HTTPAdapter


class DownloadService:
    def run(self, memory: Memory) -> tuple[bool, str | None]:
        file_path = None

        response = self._download_memory(memory)
        if response.status_code >= 400:
            self._log_fetch_failure(response.status_code, memory)
            return False

        file_path = self._store_downloaded_memory(memory, response)
        MediaDispatcher.process_media(file_path, memory)

        return file_path, True


    def _download_memory(self, memory: Memory) -> requests.Response:
        timeout = Config.cli_options['request_timeout']
        http_response = self._build_session().get(
            memory.media_download_url,
            timeout=timeout
        )
        return http_response


    def _build_session(self) -> requests.Session:
        http_session = requests.Session()
        adapter = self._create_http_adapter()
        http_session.mount("https://", adapter)
        return http_session


    @staticmethod
    def _create_http_adapter():
        max_concurrent = Config.cli_options['max_concurrent_downloads']
        adapter = HTTPAdapter(
            pool_connections=max_concurrent,
            pool_maxsize=max_concurrent * 2,
        )
        return adapter


    @staticmethod
    def _log_fetch_failure(status_code: int, memory: Memory):
        file_name = memory.filename_with_ext
        log(f"Failed to download {file_name}", "error", status_code)


    @staticmethod
    def _store_downloaded_memory(memory: Memory, download_response: requests.Response):
        downloads_folder = Config.downloads_folder
        file_path = downloads_folder / memory.filename_with_ext

        if file_path.exists():
            file_path = FileNameResolver.resolve_unique_path(file_path)

        with open(file_path, 'wb') as f:
            f.write(download_response.content)

        return file_path
