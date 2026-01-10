from time import time


class StatsManager:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.total_files = 0
            self.start_time = time()
            self.successful_downloads_count = 0
            self.failed_downloads_count = 0
            self.total_bytes = 0
            self.errors = []
            self.completed_indices = set()
            self.initialized = True


    def reset(self):
        type(self)._instance = None
