from pathlib import Path
from typing import Set

class FileNameResolver:
    def __init__(self, base_folder: Path):
        self.used_names: Set[str] = set()
        self._seed_existing_files(base_folder)


    def _seed_existing_files(self, folder: Path) -> None:
        try:
            self.used_names = {path.name for path in folder.iterdir() if path.is_file()}
        except Exception:
            self.used_names = set()


    def resolve_unique_path(self, path: Path) -> Path:
        base_name = path.stem
        extension = path.suffix
        parent = path.parent

        candidate_file_path = path
        suffix = 1

        while candidate_file_path.name in self.used_names:
            candidate_file_path = parent / f"{base_name}_{suffix}{extension}"
            suffix += 1

        self.used_names.add(candidate_file_path.name)
        return candidate_file_path
