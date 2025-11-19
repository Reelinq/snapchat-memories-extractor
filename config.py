from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    json_path: Path = Path('data/memories_history.json')
    downloads_folder: Path = Path('downloads')

    request_timeout: int = 30
    ffmpeg_timeout: int = 60


    def __post_init__(self):
        self.downloads_folder.mkdir(exist_ok=True)
