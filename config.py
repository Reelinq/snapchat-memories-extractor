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
    apply_overlay: bool = True  # Default is to apply PNG overlay
    write_metadata: bool = True  # Default is to write metadata to photos and videos
    max_attempts: int = 3  # Number of times to run the entire download process
    log_level: int = logging.INFO  # Logging level
    strict_location: bool = False  # Fail downloads when location metadata is missing

    def __post_init__(self):
        self.downloads_folder.mkdir(exist_ok=True)
        self.logs_folder.mkdir(exist_ok=True)

    @classmethod
    def from_args(cls) -> 'Config':
        parser = argparse.ArgumentParser(description='Snapchat Memories Downloader')
        parser.add_argument(
           '--concurrent', '-c',
            type=int,
            default=5,
            metavar='N',
            help='Concurrent downloads (default: 5). Short: -c'
        )
        parser.add_argument(
            '--no-overlay', '-O',
            action='store_true',
            help='Skip applying PNG overlay (default: overlay applied). Short: -O'
        )
        parser.add_argument(
            '--no-metadata', '-M',
            action='store_true',
            help='Skip writing metadata (default: metadata written). Short: -M'
        )
        parser.add_argument(
            '--attempts', '-a',
            type=int,
            default=3,
            metavar='N',
            help='Max retry attempts (default: 3). Short: -a'
        )
        parser.add_argument(
            '--strict', '-s',
            dest='strict_location',
            action='store_true',
            help='Fail downloads when location metadata is missing. Short: -s'
        )
        args = parser.parse_args()

        return cls(
            max_concurrent_downloads=args.concurrent,
            apply_overlay=not args.no_overlay,
            write_metadata=not args.no_metadata,
            max_attempts=args.attempts,
            strict_location=args.strict_location
        )
