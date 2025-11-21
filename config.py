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
        args = parser.parse_args()

        return cls(
            max_concurrent_downloads=args.concurrent,
            apply_overlay=not args.no_overlay
        )
