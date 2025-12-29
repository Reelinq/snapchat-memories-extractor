import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    # Default file and folder paths
    json_path: Path = Path('data/memories_history.json')
    downloads_folder: Path = Path('downloads')
    logs_folder: Path = Path('logs')

    # Configuration options with default values
    cli_options: dict = None

    # Ensure directories exist
    def __post_init__(self):
        self.downloads_folder.mkdir(parents=True, exist_ok=True)
        self.logs_folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def parse_log_level(level_input: str) -> int:
        base_levels = [
            ('0', 'OFF', logging.CRITICAL + 10),
            ('1', 'CRITICAL', logging.CRITICAL),
            ('2', 'ERROR', logging.ERROR),
            ('3', 'WARNING', logging.WARNING),
            ('4', 'INFO', logging.INFO),
            ('5', 'DEBUG', logging.DEBUG),
        ]
        level_map = {}
        for num, name, value in base_levels:
            level_map[num] = value
            level_map[name] = value

        level_upper = level_input.upper()
        if level_upper in level_map:
            return level_map[level_upper]
        else:
            raise argparse.ArgumentTypeError(f"Invalid log level: {level_input}. Use 0-5 or OFF/CRITICAL/ERROR/WARNING/INFO/DEBUG")

    @classmethod
    def from_args(class_reference) -> 'Config':
        parser = argparse.ArgumentParser(
            description='Snapchat Memories Downloader')
        parser.add_argument('--stream-chunk-size', '-S', type=int, default=1024, metavar='KB',
                            help='Size of each chunk in kilobytes (default: 1024, i.e. 1 MB). Short: -S')
        parser.add_argument('--ffmpeg-timeout', '-f', type=int, default=60, metavar='SECONDS',
                            help='Seconds to wait for ffmpeg operations (default: 60). Short: -f')
        parser.add_argument('--request-timeout', '-t', type=int, default=30, metavar='SECONDS',
                            help='Seconds to wait for HTTP requests (default: 30). Short: -t')
        parser.add_argument('--concurrent', '-c', type=int, default=5,
                            metavar='N', help='Concurrent downloads (default: 5). Short: -c')
        parser.add_argument('--no-overlay', '-O', default=False, action='store_true',
                            help='Skip applying PNG overlay (default: overlay applied). Short: -O')
        parser.add_argument('--no-metadata', '-M', default=False, action='store_true',
                            help='Skip writing metadata (default: metadata written). Short: -M')
        parser.add_argument('--attempts', '-a', type=int, default=3,
                            metavar='N', help='Max retry attempts (default: 3). Short: -a')
        parser.add_argument('--strict', '-s', default=False, dest='strict_location',
                            action='store_true', help='Fail downloads when location metadata is missing. Short: -s')
        parser.add_argument('--jpeg-quality', '-q', type=int, default=95,
                            metavar='N', help='JPEG quality 1-100 (default: 95). Short: -q')
        parser.add_argument('--no-jxl', '-J', default=False, action='store_true',
                            help='Skip JPGXL conversion and keep original JPEG (default: convert to lossless JPGXL). Short: -J')
        parser.add_argument('--log-level', '-l', type=class_reference.parse_log_level, default=logging.CRITICAL + 10, metavar='LEVEL',
                            help='Logging level: 0=OFF, 1=CRITICAL, 2=ERROR, 3=WARNING, 4=INFO, 5=DEBUG. Can also use names: OFF, CRITICAL, ERROR, WARNING, INFO, DEBUG (default: 0/OFF). Short: -l')
        args = parser.parse_args()

        cli_options = {
            'max_concurrent_downloads': args.concurrent,
            'apply_overlay': not args.no_overlay,
            'write_metadata': not args.no_metadata,
            'max_attempts': args.attempts,
            'strict_location': args.strict_location,
            'jpeg_quality': args.jpeg_quality,
            'convert_to_jxl': not args.no_jxl,
            'log_level': args.log_level,
            'request_timeout': args.request_timeout,
            'ffmpeg_timeout': args.ffmpeg_timeout,
            'stream_chunk_size': args.stream_chunk_size * 1024
        }

        return class_reference(cli_options=cli_options)
