import json
import threading
from pathlib import Path
from typing import Dict, List
from src.logger.log import log


class MemoriesRepository:
    def __init__(self, json_path: Path):
        self.json_path = json_path
        self._file_lock = threading.Lock()


    def get_raw_items(self) -> List[Dict]:
        data = self._load()
        if not data:
            return []

        return data.get('Saved Media', [])


    def _load(self) -> Dict:
        if not self.json_path.exists():
            log(f"Memories JSON file not found at {self.json_path}", "error", "MISS")
            return {}

        with open(self.json_path, 'r', encoding='utf-8') as file:
            return json.load(file)


    def prune(self, memory_index_to_remove: int) -> None:
        with self._file_lock:
            data = self._load()
            self._prune_item(data, memory_index_to_remove)
            self._save(data)


    @staticmethod
    def _prune_item(data: Dict, index: int) -> None:
        saved_media = data.get('Saved Media', [])
        if 0 <= index < len(saved_media):
            del saved_media[index]
        else:
            log(f"Index {index} is out of bounds for pruning.", "warning")
            pass


    def _save(self, data: Dict) -> None:
        text = json.dumps(data, ensure_ascii=False, indent=4)
        self.json_path.write_text(text, encoding='utf-8')
