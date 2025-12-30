from pathlib import Path

class FileNameResolver:
    def __init__(self, base_folder: Path):
        self.used_names = {path.name for path in base_folder.iterdir()}

    def resolve_unique_path(self, path: Path) -> Path:
        candidate_file_path = path
        file_index = 1

        while candidate_file_path.name in self.used_names:
            candidate_file_path = path.parent / \
                f"{path.stem}_{file_index}{path.suffix}"
            file_index += 1

        self.used_names.add(candidate_file_path.name)
        return candidate_file_path
