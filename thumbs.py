"""Thumbnails em disco para os cards (foto original só no preview do form)."""
from pathlib import Path

from PIL import Image

THUMB_SIZE = (320, 320)


def ensure_thumb(resolved: Path, thumbs_dir: Path) -> Path:
    """Gera thumbnail se ausente ou mais velho que a fonte. Retorna caminho do thumb."""
    thumbs_dir.mkdir(exist_ok=True)
    thumb = thumbs_dir / resolved.name
    if not thumb.is_file() or thumb.stat().st_mtime < resolved.stat().st_mtime:
        img = Image.open(resolved).convert("RGB")
        img.thumbnail(THUMB_SIZE)
        img.save(thumb, format="JPEG", quality=70)
    return thumb
