import json
import threading
from pathlib import Path
from typing import Dict, List, Set


class MemoryRepository:
    def __init__(self, json_path: Path):
        self.json_path = json_path
        self._file_lock = threading.Lock()


    def load(self) -> Dict:
        with open(self.json_path, 'r', encoding='utf-8') as file:
            return json.load(file)


    def prune(self, success_indices: Set[int]) -> None:
        if not success_indices:
            return

        with self._file_lock:
            data = self.load()
            raw_items = data.get('Saved Media', [])

            remaining = [item for i, item in enumerate(raw_items) if i not in success_indices]
            data['Saved Media'] = remaining

            with open(self.json_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)


    def get_raw_items(self) -> List[Dict]:
        data = self.load()
        return data.get('Saved Media', [])
