from abc import ABC, abstractmethod
from pathlib import Path
from models import Memory
from services.overlay_service import OverlayService
from services.metadata_service import MetadataService
from typing import Optional


class MediaProcessor(ABC):
    def __init__(self, overlay_service: OverlayService, metadata_service: MetadataService):
        self.overlay_service = overlay_service
        self.metadata_service = metadata_service

    @abstractmethod
    def apply_overlay(
        self,
        media_bytes: bytes,
        overlay_bytes: bytes,
        output_path: Optional[Path] = None,
        ffmpeg_timeout: int = 60
    ) -> bytes:
        pass

    @abstractmethod
    def write_metadata(self, memory: Memory, file_path: Path, ffmpeg_timeout: int = 60) -> None:
        pass


class ImageProcessor(MediaProcessor):
    def apply_overlay(
        self,
        media_bytes: bytes,
        overlay_bytes: bytes,
        output_path: Optional[Path] = None,
        ffmpeg_timeout: int = 60
    ) -> bytes:
        return self.overlay_service.apply_overlay_to_image(media_bytes, overlay_bytes)

    def write_metadata(self, memory: Memory, file_path: Path, ffmpeg_timeout: int = 60) -> None:
        self.metadata_service._write_image_metadata(memory, file_path)


class VideoProcessor(MediaProcessor):
    def apply_overlay(
        self,
        media_bytes: bytes,
        overlay_bytes: bytes,
        output_path: Optional[Path] = None,
        ffmpeg_timeout: int = 60
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

    def write_metadata(self, memory: Memory, file_path: Path, ffmpeg_timeout: int = 60) -> None:
        self.metadata_service._write_video_metadata(memory, file_path, ffmpeg_timeout)


def get_media_processor(
    media_type: str,
    overlay_service: OverlayService,
    metadata_service: MetadataService
) -> MediaProcessor:
    if media_type == "Image":
        return ImageProcessor(overlay_service, metadata_service)
    else:
        return VideoProcessor(overlay_service, metadata_service)
