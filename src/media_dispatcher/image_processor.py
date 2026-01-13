from src.memories import Memory
from pathlib import Path
from src.config import Config
from src.converters import JXLConverter
from src.metadata import ImageMetadataWriter


def process_image(memory: Memory, file_path: Path, config: Config):
    convert_to_jxl = config.from_args().cli_options['convert_to_jxl']
    write_metadata = config.from_args().cli_options['write_metadata']

    if write_metadata:
        ImageMetadataWriter().write_image_metadata(memory, file_path, config)

    if convert_to_jxl:
        file_path = JXLConverter().run(file_path, config)

    return file_path
