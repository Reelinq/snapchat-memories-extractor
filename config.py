import argparse
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    json_path: Path = Path('data/memories_history.json')
    downloads_folder: Path = Path('downloads')

    request_timeout: int = 30
    ffmpeg_timeout: int = 60
    max_concurrent_downloads: int = 5
    apply_overlay: bool = True  # Default is to apply PNG overlay
    write_metadata: bool = True  # Default is to write metadata to photos and videos
    max_attempts: int = 3  # Number of times to run the entire download process


    def __post_init__(self):
        self.downloads_folder.mkdir(exist_ok=True)

    @classmethod
    def from_args(cls) -> 'Config':
        parser = argparse.ArgumentParser(description='Snapchat Memories Downloader')
        parser.add_argument(
            '--concurrent',
            type=int,
            default=5,
            metavar='N',
            help='Number of concurrent downloads (default: 5)'
        )
        parser.add_argument(
            '--no-overlay',
            action='store_true',
            help='Skip applying PNG overlay on media (default: overlay is applied)'
        )
        parser.add_argument(
            '--no-metadata',
            action='store_true',
            help='Skip writing metadata to photos and videos (default: metadata is written)'
        )
        parser.add_argument(
            '--attempts',
            type=int,
            default=3,
            metavar='N',
            help='Number of times to run the entire download process (default: 3)'
        )
        args = parser.parse_args()

        return cls(
            max_concurrent_downloads=args.concurrent,
            apply_overlay=not args.no_overlay,
            write_metadata=not args.no_metadata,
            max_attempts=args.attempts
        )
