from pathlib import Path
from src.config.main import Config


class FileNameResolver:
    def run(self, path: Path) -> Path:
        used_names = [path.name for path in Config.downloads_folder.iterdir()]
        candidate = self._next_available(path, used_names)
        used_names.append(candidate.name)
        return candidate


    def _next_available(self, path: Path, used_names: list[str]) -> Path:
        candidate = path
        index = 1
        while self._is_used(candidate, used_names):
            candidate = self._with_index(path, index)
            index += 1
        return candidate


    def _is_used(self, path: Path, used_names: list[str]) -> bool:
        return path.name in used_names


    @staticmethod
    def _with_index(path: Path, index: int) -> Path:
        return path.parent / f"{path.stem}_{index}{path.suffix}"
