from pathlib import Path
from src import FileNameResolver
from src.memories import Memory
from src.config import Config
from src.media_dispatcher import process_media
from src.logger import log
from requests import Response, Session, adapters


class DownloadService:
    def __init__(self, memory: Memory):
        self.memory = memory


    def run(self) -> tuple[bool, str | None]:
        file_path = None

        response = self._download_memory()
        if response.status_code >= 400:
            self._log_fetch_failure(response.status_code)
            return None, False

        self.memory.is_zip = self._is_zip_response(response)

        file_path = self._store_downloaded_memory(response)
        file_path = process_media(self.memory, file_path)

        return file_path, True


    def _download_memory(self) -> Response:
        timeout = Config.cli_options['request_timeout']
        http_response = self._build_session().get(
            self.memory.media_download_url,
            timeout=timeout
        )
        return http_response


    def _build_session(self) -> Session:
        http_session = Session()
        adapter = self._create_http_adapter()
        http_session.mount("https://", adapter)
        return http_session


    def _create_http_adapter(self) -> adapters.HTTPAdapter:
        max_concurrent = Config.cli_options['max_concurrent_downloads']
        adapter = adapters.HTTPAdapter(
            pool_connections=max_concurrent,
            pool_maxsize=max_concurrent * 2,
        )
        return adapter


    def _log_fetch_failure(self, status_code: int):
        file_name = self.memory.filename_with_ext
        log(f"Failed to download {file_name}", "error", status_code)


    @staticmethod
    def _is_zip_response(response: Response) -> bool:
        content_type = response.headers.get("Content-Type", "")
        return content_type.lower() == "application/zip"


    def _store_downloaded_memory(self, download_response: Response):
        file_path = Config.downloads_folder / self.memory.filename_with_ext

        if file_path.exists():
            file_path = FileNameResolver(file_path).run()

        with open(file_path, 'wb') as f:
            f.write(download_response.content)

        return file_path
