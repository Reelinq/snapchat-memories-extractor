from src.models import Memory
from pathlib import Path
from src.config.main import Config
from src.converters.jxl_converter import JXLConverter
from src.metadata.image_metadata_writer import ImageMetadataWriter


def process_image(memory: Memory, file_path: Path):
    convert_to_jxl = Config.from_args().cli_options['convert_to_jxl']
    write_metadata = Config.from_args().cli_options['write_metadata']

    if write_metadata:
        ImageMetadataWriter().write_image_metadata(memory, file_path)

    if convert_to_jxl:
        file_path = JXLConverter().run(file_path)

    return file_path
