from pathlib import Path
from typing import Set

class FileNameResolver:
    def __init__(self, base_folder: Path):
        self.used_names: Set[str] = set()
        self._seed_existing_files(base_folder)


    def _seed_existing_files(self, folder: Path) -> None:
        try:
            self.used_names = {p.name for p in folder.iterdir() if p.is_file()}
        except Exception:
            self.used_names = set()


    def resolve_unique_path(self, path: Path) -> Path:
        base_name = path.stem
        ext = path.suffix
        parent = path.parent

        candidate = path
        suffix = 1

        while candidate.name in self.used_names:
            candidate = parent / f"{base_name}_{suffix}{ext}"
            suffix += 1

        self.used_names.add(candidate.name)
        return candidate
