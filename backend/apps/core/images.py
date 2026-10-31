"""Image helpers: downscale uploads so the free hosting disk lasts longer."""

from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def shrink_image_field(field_file, max_dim=None, quality=85):
    """Resize an ImageField's file in place (keeps aspect ratio, fixes EXIF rotation).

    Call before the model is saved, right after a new file was assigned.
    """
    if not field_file or getattr(field_file, "_committed", True):
        return
    max_dim = max_dim or settings.IMAGE_MAX_DIMENSION
    try:
        field_file.open()
        img = Image.open(field_file)
        img = ImageOps.exif_transpose(img)
    except Exception:  # not an image Pillow understands; let validation handle it
        return
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    name = Path(field_file.name).stem + ".jpg"
    field_file.save(name, ContentFile(buf.getvalue()), save=False)
