"""Resolução e persistência de fotos dos carros."""
import base64
import io
import time
from pathlib import Path

from PIL import Image

from thumbs import ensure_thumb

PHOTOS_DIR = Path(__file__).parent.parent / "photos"
PHOTOS_DIR.mkdir(exist_ok=True)
THUMBS_DIR = PHOTOS_DIR / "thumbs"
# servido pelo Streamlit (server.enableStaticServing) em /app/static/...
STATIC_DIR = PHOTOS_DIR.parent / "static"
STATIC_THUMBS_DIR = STATIC_DIR / "thumbs"
STATIC_THUMBS_DIR.mkdir(parents=True, exist_ok=True)


def resolve_photo(path: str) -> Path | None:
    """Resolve a stored foto_path to an existing file Path.

    Handles three stored forms: relative ('photos/x.jpg'), absolute
    (legacy, e.g. 'D:\\Code\\...'), and bare filename. Returns None if no
    matching file exists so the caller falls back to the color swatch.
    """
    if not path:
        return None
    p = Path(path)
    if p.is_absolute():
        candidates = [p, PHOTOS_DIR / p.name]
    else:
        candidates = [PHOTOS_DIR.parent / p, PHOTOS_DIR / p.name]
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def img_b64(path) -> str:
    """Read resolved image file, return base64 string."""
    resolved = resolve_photo(str(path))
    if resolved is None:
        raise FileNotFoundError(path)
    return base64.b64encode(resolved.read_bytes()).decode()


def img_thumb_url(path) -> str | None:
    """URL do thumbnail servido como arquivo estático (gera sob demanda).

    Cards usam isto, não a foto original: o rerun transmite só o endereço e
    o navegador cacheia a imagem entre reruns. None se não houver foto."""
    resolved = resolve_photo(str(path))
    if resolved is None:
        return None
    thumb = ensure_thumb(resolved, STATIC_THUMBS_DIR)
    return f"/app/static/thumbs/{thumb.name}"


def save_photo(photo_bytes: bytes, modelo: str, old_path: str | None = None) -> str:
    """Save photo to disk, return relative path. Remove previous photo when replacing."""
    if photo_bytes[:4] == b"RIFF" and photo_bytes[8:12] == b"WEBP":
        img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        photo_bytes = buf.getvalue()
    ts = int(time.time() * 1000)
    safe = "".join(c if c.isalnum() else "_" for c in modelo)[:30]
    filename = f"{safe}_{ts}.jpg"
    (PHOTOS_DIR / filename).write_bytes(photo_bytes)
    remove_photo(old_path)
    return f"photos/{filename}"


def remove_photo(path: str | None) -> None:
    """Delete previous photo file if it lives inside PHOTOS_DIR."""
    resolved = resolve_photo(path or "")
    if resolved is None:
        return
    try:
        if resolved.is_relative_to(PHOTOS_DIR.resolve()) and resolved.is_file():
            resolved.unlink()
            for thumbs_dir in (THUMBS_DIR, STATIC_THUMBS_DIR):
                thumb = thumbs_dir / resolved.name
                if thumb.is_file():
                    thumb.unlink()
    except OSError:
        pass
