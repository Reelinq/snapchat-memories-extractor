from functools import wraps
from typing import Callable, Any, Dict, List
import requests
import zipfile
from src.logger import get_logger

logger = get_logger()

class LocationMissingError(Exception):
    pass

ERROR_DESCRIPTIONS = {
    '401': 'Unauthorized - Invalid credentials',
    '403': 'Forbidden - Link expired. Re-export memories_history.json',
    '404': 'Not found - Resource no longer exists',
    '408': 'Request timed out',
    '410': 'Gone - Link permanently expired',
    '429': 'Rate limited - Too many requests',
    '502': 'Bad gateway - Server temporarily unavailable',
    'NET': 'Network error - Connection failed',
    'ZIP': 'ZIP processing error - Failed to extract media',
    'FILE': 'File processing error - Failed to write/read file',
    'DL': 'Download error - Failed to download file',
    'OVR': 'Overlay error - Failed to apply overlay',
    'LOC': 'Missing required location metadata',
    'ERR': 'Unexpected error',
}

def get_error_description(error_code: str) -> str:
    error_code_str = str(error_code)

    if error_code_str in ERROR_DESCRIPTIONS:
        return ERROR_DESCRIPTIONS[error_code_str]

    if error_code_str.isdigit():
        return f"HTTP {error_code_str} response"

    return 'Unexpected error'


def determine_error_code(exception: Exception) -> str:
    if isinstance(exception, LocationMissingError):
        return 'LOC'

    if isinstance(exception, requests.HTTPError):
        if exception.response is not None:
            return str(exception.response.status_code)
        return 'NET'

    if isinstance(exception, (
        requests.ConnectionError,
        requests.Timeout,
        requests.RequestException
    )):
        return 'NET'

    if isinstance(exception, (zipfile.BadZipFile, zipfile.LargeZipFile)):
        return 'ZIP'

    if isinstance(exception, (
        FileNotFoundError,
        PermissionError,
        OSError,
        IOError
    )):
        return 'FILE'

    return 'ERR'

def record_error(error: Dict[str, str], error_list: List[Dict[str, str]]) -> None:
    error_code = error.get('code', 'ERR')
    filename = error.get('filename', 'unknown')
    url = error.get('url', '')

    error_code_description = get_error_description(error_code)

    extra_data = {
        "error_code": error_code,
        "error_code_description": error_code_description,
        "filename": filename,
        "url": url,
    }

    error_description_suffix = f" - {error_code_description}" if error_code_description else ""
    url_suffix = f" url={url}" if url else ""

    logger.error(
        f"Download failed: {filename} (code: {error_code}{error_description_suffix}){url_suffix}",
        extra={"extra_data": extra_data},
    )

    for handler in logger.handlers:
        handler.flush()

    error_list.append(error)

def handle_errors(return_on_error: Any = False):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                error_code = determine_error_code(e)

                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)

                memory = kwargs.get('memory') or (
                    args[1] if len(args) > 1 else None)

                if memory and args and hasattr(args[0], 'errors'):
                    error = {
                        'filename': memory.filename_with_ext,
                        'url': memory.media_download_url,
                        'code': error_code
                    }
                    record_error(error, args[0].errors)

                return return_on_error

        return wrapper
    return decorator
