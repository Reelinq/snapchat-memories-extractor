from PIL import Image
from io import BytesIO


def compose_image(image_bytes: bytes, overlay_bytes: bytes, quality: int = 95) -> bytes:
    base_image = Image.open(BytesIO(image_bytes))
    overlay_image = Image.open(BytesIO(overlay_bytes))

    base_image = _ensure_rgba(base_image)
    overlay_image = _ensure_rgba(overlay_image)

    # In some cases the overlay image is mismatched by 1 pixel
    overlay_image = _resize_to_match(overlay_image, base_image.size)

    combined_image = Image.alpha_composite(base_image, overlay_image)
    combined_rgb_image = combined_image.convert('RGB')

    return _save_image_to_memory(combined_rgb_image, format='JPEG', quality=quality)

def _ensure_rgba(image: Image.Image) -> Image.Image:
    if image.mode != 'RGBA':
        return image.convert('RGBA')
    return image


def _resize_to_match(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    if image.size != target_size:
        return image.resize(target_size, Image.Resampling.LANCZOS)
    return image


def _save_image_to_memory(image: Image.Image, format: str, quality: int) -> bytes:
    # Save image to memory buffer instead of disk for faster processing
    buffer = BytesIO()
    image.save(buffer, format=format, quality=quality)
    return buffer.getvalue()
