import os

from PIL import Image

from thumbs import ensure_thumb


def test_ensure_thumb_generates_scaled_copy(tmp_path):
    src = tmp_path / "a.jpg"
    Image.new("RGB", (800, 600), (255, 0, 0)).save(src)
    thumbs = tmp_path / "thumbs"

    thumb = ensure_thumb(src, thumbs)

    assert thumb.parent == thumbs
    assert max(Image.open(thumb).size) == 320


def test_ensure_thumb_reuses_fresh_cache(tmp_path):
    src = tmp_path / "a.jpg"
    Image.new("RGB", (100, 100)).save(src)
    thumbs = tmp_path / "thumbs"
    first = ensure_thumb(src, thumbs)
    first_mtime = first.stat().st_mtime_ns

    ensure_thumb(src, thumbs)

    assert first.stat().st_mtime_ns == first_mtime  # não regenerou


def test_ensure_thumb_regenerates_when_stale(tmp_path):
    src = tmp_path / "a.jpg"
    Image.new("RGB", (100, 100)).save(src)
    thumbs = tmp_path / "thumbs"
    ensure_thumb(src, thumbs)
    thumb = thumbs / "a.jpg"
    old = thumb.stat().st_mtime_ns - 1_000_000_000  # -1s: gerar thumb custa >1ms
    os.utime(thumb, ns=(old, old))  # thumb mais velho que a fonte

    ensure_thumb(src, thumbs)

    assert thumb.stat().st_mtime_ns > old  # regenerou
