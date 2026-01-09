from pathlib import Path


class FileNameResolver:
    def __init__(self, base_folder: Path):
        self.used_names = [path.name for path in base_folder.iterdir()]

    def resolve_unique_path(self, path: Path) -> Path:
        candidate = self._next_available(path)
        self.used_names.append(candidate.name)
        return candidate

    def _next_available(self, path: Path) -> Path:
        candidate = path
        index = 1
        while self._is_used(candidate):
            candidate = self._with_index(path, index)
            index += 1
        return candidate

    def _is_used(self, path: Path) -> bool:
        return path.name in self.used_names

    @staticmethod
    def _with_index(path: Path, index: int) -> Path:
        return path.parent / f"{path.stem}_{index}{path.suffix}"
