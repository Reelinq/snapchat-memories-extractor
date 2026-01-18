from pathlib import Path


def ensure_directories(downloads_folder: Path, logs_folder: Path):
    downloads_folder.mkdir(parents=True, exist_ok=True)
    logs_folder.mkdir(parents=True, exist_ok=True)
