from pathlib import Path
from src.config import Config


class FileNameResolver:
    def __init__(self, path: Path):
        self.path = path


    def run(self) -> Path:
        used_names = [path.name for path in Config.downloads_folder.iterdir()]
        candidate = self._next_available(used_names)
        used_names.append(candidate.name)
        return candidate


    def _next_available(self, used_names: list[str]) -> Path:
        candidate = self.path
        index = 1
        while self._is_used(used_names):
            candidate = self._with_index(index)
            index += 1
        return candidate


    def _is_used(self, used_names: list[str]) -> bool:
        return self.path.name in used_names


    def _with_index(self, index: int) -> Path:
        return self.path.parent / f"{self.path.stem}_{index}{self.path.suffix}"
