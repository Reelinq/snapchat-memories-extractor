from config import Config
from downloader import MemoryDownloader

if __name__ == "__main__":
    config = Config.from_args()
    downloader = MemoryDownloader(config)
    downloader.run()
