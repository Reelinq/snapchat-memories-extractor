import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    json_path: Path = Path('data/memories_history.json')
    downloads_folder: Path = Path('downloads')
    logs_folder: Path = Path('logs')

    request_timeout: int = 30
    ffmpeg_timeout: int = 60
    max_concurrent_downloads: int = 5
    stream_chunk_size: int = 1024 * 1024  # 1 MB chunks for streaming
    prune_batch_size: int = 25  # Commit JSON after N successes (0 = only at end)
    jpeg_quality: int = 95  # JPEG encode quality (1-100, higher = better quality/larger files)
    apply_overlay: bool = True  # Default is to apply PNG overlay
    write_metadata: bool = True  # Default is to write metadata to photos and videos
    max_attempts: int = 3  # Number of times to run the entire download process
    log_level: int = logging.CRITICAL + 10  # Logging level (default: OFF)
    strict_location: bool = False  # Fail downloads when location metadata is missing
    convert_to_jxl: bool = True  # Default is to convert JPEG images to lossless JPGXL format

    def __post_init__(self):
        self.downloads_folder.mkdir(exist_ok=True)
        self.logs_folder.mkdir(exist_ok=True)

    @staticmethod
    def parse_log_level(level_input: str) -> int:
        level_map = {
            # Numbers
            '0': logging.CRITICAL + 10,
            '1': logging.CRITICAL,
            '2': logging.ERROR,
            '3': logging.WARNING,
            '4': logging.INFO,
            '5': logging.DEBUG,
            # Names
            'OFF': logging.CRITICAL + 10,
            'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
        }

        level_upper = level_input.upper()
        if level_upper in level_map:
            return level_map[level_upper]
        else:
            raise argparse.ArgumentTypeError(f"Invalid log level: {level_input}. Use 0-5 or OFF/CRITICAL/ERROR/WARNING/INFO/DEBUG")

    @classmethod
    def from_args(class_reference) -> 'Config':
        command_line_argument_parser = argparse.ArgumentParser(description='Snapchat Memories Downloader')
        command_line_argument_parser.add_argument(
           '--concurrent', '-c',
            type=int,
            default=5,
            metavar='N',
            help='Concurrent downloads (default: 5). Short: -c'
        )
        command_line_argument_parser.add_argument(
            '--no-overlay', '-O',
            action='store_true',
            help='Skip applying PNG overlay (default: overlay applied). Short: -O'
        )
        command_line_argument_parser.add_argument(
            '--no-metadata', '-M',
            action='store_true',
            help='Skip writing metadata (default: metadata written). Short: -M'
        )
        command_line_argument_parser.add_argument(
            '--attempts', '-a',
            type=int,
            default=3,
            metavar='N',
            help='Max retry attempts (default: 3). Short: -a'
        )
        command_line_argument_parser.add_argument(
            '--strict', '-s',
            dest='strict_location',
            action='store_true',
            help='Fail downloads when location metadata is missing. Short: -s'
        )
        command_line_argument_parser.add_argument(
            '--jpeg-quality', '-q',
            type=int,
            default=95,
            metavar='Q',
            help='JPEG quality 1-100 (default: 95). Short: -q'
        )
        command_line_argument_parser.add_argument(
            '--no-jxl', '-J',
            action='store_true',
            help='Skip JPGXL conversion and keep original JPEG (default: convert to lossless JPGXL). Short: -J'
        )
        command_line_argument_parser.add_argument(
            '--log-level', '-l',
            type=class_reference.parse_log_level,
            default=logging.CRITICAL + 10,
            metavar='LEVEL',
            help='Logging level: 0=OFF, 1=CRITICAL, 2=ERROR, 3=WARNING, 4=INFO, 5=DEBUG. Can also use names: OFF, CRITICAL, ERROR, WARNING, INFO, DEBUG (default: 0/OFF). Short: -l'
        )
        parsed_arguments = command_line_argument_parser.parse_args()

        return class_reference(
            max_concurrent_downloads=parsed_arguments.concurrent,
            apply_overlay=not parsed_arguments.no_overlay,
            write_metadata=not parsed_arguments.no_metadata,
            max_attempts=parsed_arguments.attempts,
            strict_location=parsed_arguments.strict_location,
            jpeg_quality=parsed_arguments.jpeg_quality,
            convert_to_jxl=not parsed_arguments.no_jxl,
            log_level=parsed_arguments.log_level
        )
