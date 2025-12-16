from abc import ABC, abstractmethod
from pathlib import Path
from src.models import Memory
from src.services.overlay_service import OverlayService
from src.services.metadata_service import MetadataService
from src.services.jxl_converter import JXLConverter
from typing import Optional


class MediaProcessor(ABC):
    def __init__(self, overlay_service: OverlayService, metadata_service: MetadataService, convert_to_jxl: bool = True):
        self.overlay_service = overlay_service
        self.metadata_service = metadata_service
        self.convert_to_jxl = convert_to_jxl

    @abstractmethod
    def apply_overlay(
        self,
        media_bytes: bytes,
        overlay_bytes: bytes,
        output_path: Optional[Path] = None,
        ffmpeg_timeout: int = 60,
        jpeg_quality: int = 95
    ) -> bytes:
        pass

    @abstractmethod
    def write_metadata(self, memory: Memory, file_path: Path, ffmpeg_timeout: int = 60, jpeg_quality: int = 95) -> Path:
        pass


class ImageProcessor(MediaProcessor):
    def apply_overlay(
        self,
        media_bytes: bytes,
        overlay_bytes: bytes,
        output_path: Optional[Path] = None,
        ffmpeg_timeout: int = 60,
        jpeg_quality: int = 95
    ) -> bytes:
        return self.overlay_service.apply_overlay_to_image(media_bytes, overlay_bytes, jpeg_quality)

    def write_metadata(self, memory: Memory, file_path: Path, ffmpeg_timeout: int = 60, jpeg_quality: int = 95) -> Path:
        self.metadata_service._write_image_metadata(memory, file_path, jpeg_quality)

        # Convert to JPGXL after metadata is written
        if self.convert_to_jxl and JXLConverter.is_convertible_image(file_path):
            file_path = JXLConverter.convert_to_jxl(file_path)

        return file_path


class VideoProcessor(MediaProcessor):
    def apply_overlay(
        self,
        media_bytes: bytes,
        overlay_bytes: bytes,
        output_path: Optional[Path] = None,
        ffmpeg_timeout: int = 60,
        jpeg_quality: int = 95
    ) -> bytes:
        if output_path is None:
            raise ValueError("output_path is required for video overlay processing")

        self.overlay_service.apply_overlay_to_video(
            media_bytes,
            overlay_bytes,
            output_path,
            ffmpeg_timeout
        )
        # Return original bytes since file is written directly
        return media_bytes

    def write_metadata(self, memory: Memory, file_path: Path, ffmpeg_timeout: int = 60, jpeg_quality: int = 95) -> Path:
        self.metadata_service._write_video_metadata(memory, file_path, ffmpeg_timeout)
        return file_path


def get_media_processor(
    media_type: str,
    overlay_service: OverlayService,
    metadata_service: MetadataService,
    convert_to_jxl: bool = True
) -> MediaProcessor:
    if media_type == "Image":
        return ImageProcessor(overlay_service, metadata_service, convert_to_jxl)
    else:
        return VideoProcessor(overlay_service, metadata_service, convert_to_jxl)
