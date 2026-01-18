from time import time


class StatsManager:
    current_attempt = 0
    total_files = 0
    start_time = time()
    successful_downloads_count = 0
    failed_downloads_count = 0
    total_bytes = 0
    errors = []
    completed_indices = set()

    @classmethod
    def new_attempt(cls) -> None:
        cls.current_attempt += 1
        cls.total_files = cls.failed_downloads_count
        cls.start_time = time()
        cls.successful_downloads_count = 0
        cls.failed_downloads_count = 0
        cls.total_bytes = 0
        cls.errors = []
        cls.completed_indices = set()
