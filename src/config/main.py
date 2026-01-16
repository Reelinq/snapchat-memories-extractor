from dataclasses import dataclass
from pathlib import Path
from src.config.cli_args import get_cli_args
from src.config.cli_options import build_cli_options
from src.config.paths import ensure_directories

@dataclass
class Config:
    json_path: Path = Path('data/memories_history.json')
    downloads_folder: Path = Path('downloads')
    logs_folder: Path = Path('logs')
    cli_options: dict = None

    def __post_init__(self):
        ensure_directories(self.downloads_folder, self.logs_folder)


    @classmethod
    def initialize_config(cls):
        args = get_cli_args()
        cls.cli_options = build_cli_options(args)
        cls._ensure_directories()


    @classmethod
    def _ensure_directories(cls):
        cls.downloads_folder.mkdir(parents=True, exist_ok=True)
        cls.logs_folder.mkdir(parents=True, exist_ok=True)
