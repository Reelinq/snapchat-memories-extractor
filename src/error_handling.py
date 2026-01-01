from functools import wraps
from typing import Callable, Any, Dict, List, Optional
import requests
import zipfile
from concurrent.futures import Future

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
    'INT': 'Interrupted by user',
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
    if isinstance(exception, KeyboardInterrupt):
        return 'INT'

    if isinstance(exception, LocationMissingError):
        return 'LOC'

    if isinstance(exception, requests.HTTPError) and exception.response:
        return str(exception.response.status_code)

    if isinstance(exception, requests.RequestException):
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


def safe_future_result(future: Future, default_on_error: Any = False):
    try:
        return future.result()
    except Exception as exception:
        logger.error(f"Thread executor error: {exception}", exc_info=True)
        return default_on_error


def handle_errors(return_on_error: Any = False):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                error_code = determine_error_code(e)

                if isinstance(e, KeyboardInterrupt):
                    logger.warning(f"Interrupted in {func.__name__}")
                else:
                    logger.error(
                        f"Error in {func.__name__}: {e}", exc_info=True)

                memory = kwargs.get('memory')
                if not memory:
                    candidate = args[2] if len(args) > 2 else (
                        args[1] if len(args) > 1 else None)
                    if candidate and hasattr(candidate, 'media_download_url'):
                        memory = candidate

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


def handle_batch_errors(cleanup_method: Optional[str] = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except KeyboardInterrupt:
                logger.warning("Download interrupted by user")

                if args and hasattr(args[0], '_interrupted'):
                    args[0]._interrupted = True

                if args and hasattr(args[0], 'executor'):
                    args[0].executor.shutdown(wait=True, cancel_futures=True)

                if cleanup_method and args and hasattr(args[0], cleanup_method):
                    getattr(args[0], cleanup_method)(force=True)

                if args and hasattr(args[0], '_convert_remaining_jpegs_on_interrupt'):
                    args[0]._convert_remaining_jpegs_on_interrupt()

                raise

            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                raise

        return wrapper
    return decorator


def handle_app_errors(exit_code_on_error: int = 1):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            exit_code = 0
            exit_reason = "normal"

            try:
                result = func(*args, **kwargs)
                logger.info("Application completed successfully")
                return result

            except KeyboardInterrupt:
                logger.warning("Process interrupted by user (Ctrl+C)")
                exit_code = 0
                exit_reason = "keyboard_interrupt"

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                exit_code = exit_code_on_error
                exit_reason = "error"

            finally:
                if args and hasattr(args[0], 'close'):
                    try:
                        args[0].close()
                    except KeyboardInterrupt:
                        logger.warning("Cleanup interrupted by user")
                        exit_code = 0
                        exit_reason = "keyboard_interrupt_during_cleanup"

                import time
                time.sleep(0.1)

                logger.info(
                    f"Application ended - reason: {exit_reason}, exit_code: {exit_code}")

                import sys
                sys.exit(exit_code)

        return wrapper
    return decorator
