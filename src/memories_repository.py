import json
from typing import Dict, List
from src.logger.log import log
from src.config.main import Config


class MemoriesRepository:
    def get_raw_items(self) -> List[Dict]:
        data = self._load()
        if not data:
            return []

        return data.get('Saved Media', [])


    @staticmethod
    def _load() -> Dict:
        if not Config.json_path.exists():
            log(f"Memories JSON file not found at {Config.json_path}", "error", "MISS")
            return {}

        with open(Config.json_path, 'r', encoding='utf-8') as file:
            return json.load(file)


    def prune_by_media_download_url(self, media_download_url: str) -> None:
        data = self._load()
        saved_media = data.get('Saved Media', [])
        for index, item in enumerate(saved_media):
            if item.get('Media Download Url') != media_download_url:
                continue
            del saved_media[index]
            self._save(data)
            return
        log(f"Media Download Url {media_download_url} not found for pruning.", "warning")


    @staticmethod
    def _save(data: Dict) -> None:
        text = json.dumps(data, ensure_ascii=False, indent=4)
        Config.json_path.write_text(text, encoding='utf-8')
