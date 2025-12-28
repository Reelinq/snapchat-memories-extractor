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


    def __post_init__(self):
        self.downloads_folder.mkdir(exist_ok=True)
        self.logs_folder.mkdir(exist_ok=True)

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
            default=False,
            help='Skip applying PNG overlay (default: overlay applied). Short: -O'
        )
        command_line_argument_parser.add_argument(
            '--no-metadata', '-M',
            action='store_true',
            default=False,
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
            default=False,
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
            default=False,
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
