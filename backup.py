"""Backup da coleção: exportar/importar ZIP (collection.db + fotos referenciadas)."""
import io
import shutil
import sqlite3
import zipfile
from pathlib import Path

from storage import init_db


def _referenced_names(db_path: Path) -> set[str]:
    """Basenames das fotos referenciadas em cars.foto_path ([] se DB ausente)."""
    if not db_path.is_file():
        return set()
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT foto_path FROM cars WHERE foto_path != ''").fetchall()
    except sqlite3.DatabaseError:
        return set()
    finally:
        conn.close()
    return {Path(r[0]).name for r in rows}


def export_zip(db_path: Path, photos_dir: Path) -> bytes:
    """ZIP com collection.db + fotos referenciadas (thumbs fora)."""
    buf = io.BytesIO()
    # backup API: cópia consistente mesmo com outra sessão escrevendo no DB
    tmp = db_path.with_name(db_path.stem + "_export.tmpdb")
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(tmp))
    src.backup(dst)
    src.close()
    dst.close()
    try:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(tmp, "collection.db")
            for name in sorted(_referenced_names(tmp)):
                p = photos_dir / name
                if p.is_file():
                    zf.write(p, f"photos/{name}")
    finally:
        tmp.unlink(missing_ok=True)
    return buf.getvalue()


def import_zip(db_path: Path, photos_dir: Path, data: bytes) -> int:
    """Substitui a coleção inteira pelo ZIP. Retorna nº de carros importados."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        if "collection.db" not in names:
            raise ValueError("ZIP sem collection.db")
        old = _referenced_names(db_path)
        db_bytes = zf.read("collection.db")
        photos = {Path(n).name: zf.read(n) for n in names
                  if n.startswith("photos/") and not n.endswith("/")}
    tmp = db_path.with_name(db_path.stem + "_import.tmpdb")
    tmp.write_bytes(db_bytes)
    conn = sqlite3.connect(str(tmp))
    try:  # valida schema antes de trocar a base atual
        conn.execute("SELECT id, modelo, foto_path FROM cars LIMIT 1").fetchone()
    except sqlite3.DatabaseError as e:
        conn.close()
        tmp.unlink(missing_ok=True)
        raise ValueError(f"collection.db inválido: {e}") from e
    n_cars = conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
    conn.close()
    tmp.replace(db_path)
    init_db()  # migrações cobrem schema de versões antigas
    for name, content in photos.items():
        (photos_dir / name).write_bytes(content)
    for name in old - set(photos):
        (photos_dir / name).unlink(missing_ok=True)
    return n_cars


def reset_collection(db_path: Path, photos_dir: Path,
                     thumbs_dir: Path | None = None) -> int:
    """Apaga base e fotos referenciadas; recria schema vazio.

    Arquivos não referenciados (logo, etc.) sobrevivem. Retorna nº de fotos apagadas.
    """
    old = _referenced_names(db_path)
    db_path.unlink(missing_ok=True)
    if thumbs_dir and thumbs_dir.is_dir():
        shutil.rmtree(thumbs_dir)
    removed = 0
    for name in old:
        p = photos_dir / name
        if p.is_file():
            p.unlink()
            removed += 1
    init_db()
    return removed
