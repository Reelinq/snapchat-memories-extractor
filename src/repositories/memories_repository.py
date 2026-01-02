import json
import threading
from pathlib import Path
from typing import Dict, List


class MemoriesRepository:
    def __init__(self, json_path: Path):
        self.json_path = json_path
        self._file_lock = threading.Lock()

    def load(self) -> Dict:
        with open(self.json_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def get_raw_items(self) -> List[Dict]:
        data = self.load()
        return data.get('Saved Media', [])

    def prune(self, memory_index_to_remove: int) -> None:
        with self._file_lock:
            data = self.load()
            self._prune_item(data, memory_index_to_remove)
            self._save(data)

    @staticmethod
    def _prune_item(data: Dict, index: int) -> None:
        del data.get('Saved Media', [])[index]

    def _save(self, data: Dict) -> None:
        text = json.dumps(data, ensure_ascii=False, indent=4)
        self.json_path.write_text(text, encoding='utf-8')
