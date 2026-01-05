from PIL import Image
from io import BytesIO
from src import config


class ImageComposer:
    #TODO: Add concurrent processing for overlays on a higher level
    def apply_overlay(self, image_bytes: bytes, overlay_bytes: bytes) -> bytes:
        base_image = Image.open(BytesIO(image_bytes))
        overlay_image = Image.open(BytesIO(overlay_bytes))

        base_image = self._ensure_rgba(base_image)
        overlay_image = self._ensure_rgba(overlay_image)

        # In some cases the overlay image is mismatched by 1 pixel
        overlay_image = self._resize_to_match(overlay_image, base_image.size)

        combined_image = Image.alpha_composite(base_image, overlay_image)
        combined_rgb_image = combined_image.convert('RGB')

        quality = config.cli_options['jpeg_quality']

        return self._save_image_to_memory(combined_rgb_image, format='JPEG', quality=quality)


    @staticmethod
    def _ensure_rgba(image: Image.Image) -> Image.Image:
        if image.mode != 'RGBA':
            return image.convert('RGBA')
        return image


    @staticmethod
    def _resize_to_match(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
        if image.size != target_size:
            return image.resize(target_size, Image.Resampling.LANCZOS)
        return image


    @staticmethod
    def _save_image_to_memory(image: Image.Image, format: str, quality: int) -> bytes:
        # Save image to memory buffer instead of disk for faster processing
        buffer = BytesIO()
        image.save(buffer, format=format, quality=quality)
        return buffer.getvalue()
