import threading


class StatsManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.successful_downloads_count = 0
        self.failed_downloads_count = 0
        self.total_bytes = 0
        self.errors = []

    def reset(self):
        with self.lock:
            self.successful_downloads_count = 0
            self.failed_downloads_count = 0
            self.total_bytes = 0
            self.errors.clear()
