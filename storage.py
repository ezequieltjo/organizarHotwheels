import sqlite3
from pathlib import Path
from models import Car, ShelfConfig, ParedeConfig

DB_PATH = Path(__file__).parent / "db" / "collection.db"
_db_path = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo TEXT NOT NULL,
    marca TEXT NOT NULL DEFAULT '',
    fabricante TEXT NOT NULL DEFAULT '',
    ano INTEGER NOT NULL DEFAULT 0,
    cor TEXT NOT NULL DEFAULT '',
    cor_hex TEXT NOT NULL DEFAULT '',
    serie_tipo TEXT NOT NULL DEFAULT '',
    favorito INTEGER NOT NULL DEFAULT 0,
    reserva INTEGER NOT NULL DEFAULT 0,
    foto_path TEXT NOT NULL DEFAULT '',
    expositor_id INTEGER,
    posicao_linha INTEGER,
    posicao_coluna INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shelf_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    linhas INTEGER NOT NULL,
    colunas INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS wall_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    linhas INTEGER NOT NULL DEFAULT 1,
    colunas INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS disabled_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shelf_id INTEGER NOT NULL,
    posicao_linha INTEGER NOT NULL,
    posicao_coluna INTEGER,
    UNIQUE(shelf_id, posicao_linha, posicao_coluna),
    FOREIGN KEY(shelf_id) REFERENCES shelf_configs(id) ON DELETE CASCADE
);
"""


def set_db_path(path):
    global _db_path
    _db_path = path


def _get_path():
    return _db_path or DB_PATH


def get_connection():
    path = _get_path()
    if isinstance(path, Path):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    # Migrate: add fabricante column if missing
    cols = [r[1] for r in conn.execute("PRAGMA table_info(cars)").fetchall()]
    if "fabricante" not in cols:
        conn.execute("ALTER TABLE cars ADD COLUMN fabricante TEXT NOT NULL DEFAULT ''")
    if "reserva" not in cols:
        conn.execute("ALTER TABLE cars ADD COLUMN reserva INTEGER NOT NULL DEFAULT 0")
    # Migrate: add wall position columns to shelf_configs
    shelf_cols = [r[1] for r in conn.execute("PRAGMA table_info(shelf_configs)").fetchall()]
    if "parede_linha" not in shelf_cols:
        conn.execute("ALTER TABLE shelf_configs ADD COLUMN parede_linha INTEGER NOT NULL DEFAULT 0")
    if "parede_coluna" not in shelf_cols:
        conn.execute("ALTER TABLE shelf_configs ADD COLUMN parede_coluna INTEGER NOT NULL DEFAULT 0")
    if "created_at" not in cols:
        conn.execute("ALTER TABLE cars ADD COLUMN created_at TIMESTAMP")
        conn.execute("ALTER TABLE cars ADD COLUMN updated_at TIMESTAMP")
        ids = [r[0] for r in conn.execute("SELECT id FROM cars ORDER BY id").fetchall()]
        for i, car_id in enumerate(ids):
            ts = f"datetime('now', '+{i} seconds')"
            conn.execute(f"UPDATE cars SET created_at = {ts}, updated_at = {ts} WHERE id = ?", (car_id,))
    elif "updated_at" not in cols:
        conn.execute("ALTER TABLE cars ADD COLUMN updated_at TIMESTAMP")
        ids = [r[0] for r in conn.execute("SELECT id FROM cars ORDER BY id").fetchall()]
        for i, car_id in enumerate(ids):
            ts = f"datetime('now', '+{i} seconds')"
            conn.execute(f"UPDATE cars SET updated_at = {ts} WHERE id = ?", (car_id,))
    conn.commit()
    conn.close()


def insert_car(car: Car) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO cars (modelo, marca, fabricante, ano, cor, cor_hex, serie_tipo,
           favorito, reserva, foto_path, expositor_id, posicao_linha, posicao_coluna, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
        (car.modelo, car.marca, car.fabricante, car.ano, car.cor, car.cor_hex, car.serie_tipo,
         int(car.favorito), int(car.reserva), car.foto_path, car.expositor_id,
         car.posicao_linha, car.posicao_coluna))
    car_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return car_id


def get_all_cars() -> list[Car]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM cars").fetchall()
    conn.close()
    return [_row_to_car(r) for r in rows]


def get_car_by_id(car_id: int) -> Car | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
    conn.close()
    return _row_to_car(row) if row else None


def update_car(car: Car) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE cars SET modelo=?, marca=?, fabricante=?, ano=?, cor=?, cor_hex=?,
           serie_tipo=?, favorito=?, reserva=?, foto_path=?, expositor_id=?,
           posicao_linha=?, posicao_coluna=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (car.modelo, car.marca, car.fabricante, car.ano, car.cor, car.cor_hex, car.serie_tipo,
         int(car.favorito), int(car.reserva), car.foto_path, car.expositor_id,
         car.posicao_linha, car.posicao_coluna, car.id))
    conn.commit()
    conn.close()


def delete_car(car_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM cars WHERE id = ?", (car_id,))
    conn.commit()
    conn.close()


def set_reserva(car_id: int, reserva: bool) -> None:
    """Marca/desmarca carro como reserva. Limpa posição ao marcar True."""
    conn = get_connection()
    if reserva:
        conn.execute(
            "UPDATE cars SET reserva=1, expositor_id=NULL, posicao_linha=NULL, posicao_coluna=NULL, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (car_id,))
    else:
        conn.execute("UPDATE cars SET reserva=0, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                     (car_id,))
    conn.commit()
    conn.close()


def _row_to_car(row) -> Car:
    return Car(
        id=row["id"], modelo=row["modelo"], marca=row["marca"],
        fabricante=row["fabricante"],
        ano=row["ano"], cor=row["cor"], cor_hex=row["cor_hex"],
        serie_tipo=row["serie_tipo"], favorito=bool(row["favorito"]),
        reserva=bool(row["reserva"]),
        foto_path=row["foto_path"], expositor_id=row["expositor_id"],
        posicao_linha=row["posicao_linha"], posicao_coluna=row["posicao_coluna"],
        created_at=row["created_at"], updated_at=row["updated_at"])


# --- ShelfConfig CRUD ---

def insert_shelf(shelf: ShelfConfig) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO shelf_configs (nome, linhas, colunas, parede_linha, parede_coluna) VALUES (?, ?, ?, ?, ?)",
        (shelf.nome, shelf.linhas, shelf.colunas, shelf.parede_linha, shelf.parede_coluna))
    shelf_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return shelf_id


def get_all_shelves() -> list[ShelfConfig]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM shelf_configs").fetchall()
    conn.close()
    return [_row_to_shelf(r) for r in rows]


def get_shelf_by_id(shelf_id: int) -> ShelfConfig | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM shelf_configs WHERE id = ?", (shelf_id,)).fetchone()
    conn.close()
    return _row_to_shelf(row) if row else None


def update_shelf(shelf: ShelfConfig) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE shelf_configs SET nome=?, linhas=?, colunas=?, parede_linha=?, parede_coluna=? WHERE id=?",
        (shelf.nome, shelf.linhas, shelf.colunas, shelf.parede_linha, shelf.parede_coluna, shelf.id))
    conn.commit()
    conn.close()
    prune_disabled_slots(shelf.id, shelf.linhas, shelf.colunas)


def delete_shelf(shelf_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM shelf_configs WHERE id = ?", (shelf_id,))
    conn.commit()
    conn.close()


def _row_to_shelf(row) -> ShelfConfig:
    return ShelfConfig(
        id=row["id"], nome=row["nome"],
        linhas=row["linhas"], colunas=row["colunas"],
        parede_linha=row["parede_linha"], parede_coluna=row["parede_coluna"])


# --- DisabledSlots CRUD ---

def get_disabled_slots(shelf_id: int) -> dict:
    """Returns {'rows': set[int], 'cells': set[tuple[int,int]]}."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT posicao_linha, posicao_coluna FROM disabled_slots WHERE shelf_id=?",
        (shelf_id,)).fetchall()
    conn.close()
    out = {"rows": set(), "cells": set()}
    for r in rows:
        if r["posicao_coluna"] is None:
            out["rows"].add(r["posicao_linha"])
        else:
            out["cells"].add((r["posicao_linha"], r["posicao_coluna"]))
    return out


def get_all_disabled_slots() -> dict[int, dict]:
    """Returns {shelf_id: {'rows': set, 'cells': set}}."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT shelf_id, posicao_linha, posicao_coluna FROM disabled_slots").fetchall()
    conn.close()
    out = {}
    for r in rows:
        s = out.setdefault(r["shelf_id"], {"rows": set(), "cells": set()})
        if r["posicao_coluna"] is None:
            s["rows"].add(r["posicao_linha"])
        else:
            s["cells"].add((r["posicao_linha"], r["posicao_coluna"]))
    return out


def set_disabled_slot(shelf_id: int, row: int, col: int | None) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO disabled_slots (shelf_id, posicao_linha, posicao_coluna) VALUES (?, ?, ?)",
        (shelf_id, row, col))
    conn.commit()
    conn.close()


def unset_disabled_slot(shelf_id: int, row: int, col: int | None) -> None:
    conn = get_connection()
    conn.execute(
        "DELETE FROM disabled_slots WHERE shelf_id=? AND posicao_linha=? AND "
        "(posicao_coluna IS ? OR posicao_coluna=?)",
        (shelf_id, row, col, col))
    conn.commit()
    conn.close()


def clear_disabled_slots(shelf_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM disabled_slots WHERE shelf_id=?", (shelf_id,))
    conn.commit()
    conn.close()


def replace_disabled_slots(shelf_id: int, rows: list[int], cells: list[tuple[int, int]]) -> None:
    """Atomically replace all disabled slots for a shelf."""
    conn = get_connection()
    conn.execute("DELETE FROM disabled_slots WHERE shelf_id=?", (shelf_id,))
    for r in rows:
        conn.execute(
            "INSERT OR IGNORE INTO disabled_slots (shelf_id, posicao_linha, posicao_coluna) VALUES (?, ?, ?)",
            (shelf_id, r, None))
    for (r, c) in cells:
        conn.execute(
            "INSERT OR IGNORE INTO disabled_slots (shelf_id, posicao_linha, posicao_coluna) VALUES (?, ?, ?)",
            (shelf_id, r, c))
    conn.commit()
    conn.close()


def prune_disabled_slots(shelf_id: int, linhas: int, colunas: int) -> None:
    """Remove bloqueios fora das dimensoes atuais da shelf."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM disabled_slots WHERE shelf_id=? AND "
        "((posicao_coluna IS NULL AND posicao_linha >= ?) OR "
        "(posicao_coluna IS NOT NULL AND (posicao_linha >= ? OR posicao_coluna >= ?)))",
        (shelf_id, linhas, linhas, colunas))
    conn.commit()
    conn.close()


# --- Position management ---

def clear_positions() -> None:
    conn = get_connection()
    conn.execute("UPDATE cars SET expositor_id=NULL, posicao_linha=NULL, posicao_coluna=NULL")
    conn.commit()
    conn.close()


def apply_positions(assignment: dict) -> None:
    """assignment: {car_id: (shelf_id, row, col)}"""
    conn = get_connection()
    for car_id, (shelf_id, row, col) in assignment.items():
        conn.execute(
            "UPDATE cars SET expositor_id=?, posicao_linha=?, posicao_coluna=? WHERE id=?",
            (shelf_id, row, col, car_id))
    conn.commit()
    conn.close()


# --- WallConfig CRUD ---

def get_wall_config() -> ParedeConfig:
    conn = get_connection()
    row = conn.execute("SELECT * FROM wall_config WHERE id = 1").fetchone()
    conn.close()
    if row:
        return ParedeConfig(id=row["id"], linhas=row["linhas"], colunas=row["colunas"])
    return ParedeConfig()


def save_wall_config(linhas: int, colunas: int) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO wall_config (id, linhas, colunas) VALUES (1, ?, ?)",
        (linhas, colunas))
    conn.commit()
    conn.close()
