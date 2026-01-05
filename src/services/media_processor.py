from abc import ABC, abstractmethod
from pathlib import Path
from src.models import Memory
from src.overlay.video_composer import VideoComposer
from src.overlay.image_composer import ImageComposer
from src.services.metadata_service import MetadataService
from src.services.jxl_converter import JXLConverter
from typing import Optional


class MediaProcessor(ABC):
    def __init__(self, overlay_service: VideoComposer, metadata_service: MetadataService, convert_to_jxl: bool = True):
        self.overlay_service = overlay_service
        self.metadata_service = metadata_service
        self.convert_to_jxl = convert_to_jxl

    @abstractmethod
    def apply_overlay(
        self,
        media_bytes: bytes,
        overlay_bytes: bytes,
        output_path: Optional[Path] = None
    ) -> bytes:
        pass

    @abstractmethod
    def write_metadata(self, memory: Memory, file_path: Path) -> Path:
        pass


class ImageProcessor(MediaProcessor):
    def apply_overlay(
        self,
        media_bytes: bytes,
        overlay_bytes: bytes,
        output_path: Optional[Path] = None,
    ) -> bytes:
        return ImageComposer().apply_overlay(media_bytes, overlay_bytes)

    def write_metadata(self, memory: Memory, file_path: Path) -> Path:
        self.metadata_service._write_image_metadata(memory, file_path)

        # Convert to JPGXL after metadata is written
        if self.convert_to_jxl and JXLConverter.is_convertible_image(file_path):
            file_path = JXLConverter.convert_to_jxl(file_path)

        return file_path


class VideoProcessor(MediaProcessor):
    def apply_overlay(
        self,
        media_bytes: bytes,
        overlay_bytes: bytes,
        output_path: Optional[Path] = None
    ) -> bytes:
        if output_path is None:
            raise ValueError("output_path is required for video overlay processing")

        self.overlay_service.apply_overlay(
            media_bytes,
            overlay_bytes,
            output_path
        )
        # Return original bytes since file is written directly
        return media_bytes

    def write_metadata(self, memory: Memory, file_path: Path) -> Path:
        self.metadata_service._write_video_metadata(memory, file_path)
        return file_path


def get_media_processor(
    media_type: str,
    overlay_service: VideoComposer,
    metadata_service: MetadataService,
    convert_to_jxl: bool = True
) -> MediaProcessor:
    if media_type == "Image":
        return ImageProcessor(overlay_service, metadata_service, convert_to_jxl)
    else:
        return VideoProcessor(overlay_service, metadata_service, convert_to_jxl)
