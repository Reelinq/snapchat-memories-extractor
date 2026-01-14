from src.memories import Memory
from pathlib import Path
from src.config import Config
from src.converters import JXLConverter
from src.metadata import ImageMetadataWriter


def process_image(memory: Memory, file_path: Path, config: Config):
    convert_to_jxl = config.cli_options['convert_to_jxl']
    write_metadata = config.cli_options['write_metadata']

    if write_metadata:
        ImageMetadataWriter(memory, file_path, config).write_image_metadata()

    if convert_to_jxl:
        file_path = JXLConverter().run(file_path, config)

    return file_path
