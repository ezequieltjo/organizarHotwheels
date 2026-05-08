import sqlite3
from pathlib import Path
from models import Car, ShelfConfig

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
    foto_path TEXT NOT NULL DEFAULT '',
    expositor_id INTEGER,
    posicao_linha INTEGER,
    posicao_coluna INTEGER
);

CREATE TABLE IF NOT EXISTS shelf_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    linhas INTEGER NOT NULL,
    colunas INTEGER NOT NULL
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
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    # Migrate: add fabricante column if missing
    cols = [r[1] for r in conn.execute("PRAGMA table_info(cars)").fetchall()]
    if "fabricante" not in cols:
        conn.execute("ALTER TABLE cars ADD COLUMN fabricante TEXT NOT NULL DEFAULT ''")
    conn.commit()
    conn.close()


def insert_car(car: Car) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO cars (modelo, marca, fabricante, ano, cor, cor_hex, serie_tipo,
           favorito, foto_path, expositor_id, posicao_linha, posicao_coluna)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (car.modelo, car.marca, car.fabricante, car.ano, car.cor, car.cor_hex, car.serie_tipo,
         int(car.favorito), car.foto_path, car.expositor_id,
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
           serie_tipo=?, favorito=?, foto_path=?, expositor_id=?,
           posicao_linha=?, posicao_coluna=? WHERE id=?""",
        (car.modelo, car.marca, car.fabricante, car.ano, car.cor, car.cor_hex, car.serie_tipo,
         int(car.favorito), car.foto_path, car.expositor_id,
         car.posicao_linha, car.posicao_coluna, car.id))
    conn.commit()
    conn.close()


def delete_car(car_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM cars WHERE id = ?", (car_id,))
    conn.commit()
    conn.close()


def _row_to_car(row) -> Car:
    return Car(
        id=row["id"], modelo=row["modelo"], marca=row["marca"],
        fabricante=row["fabricante"],
        ano=row["ano"], cor=row["cor"], cor_hex=row["cor_hex"],
        serie_tipo=row["serie_tipo"], favorito=bool(row["favorito"]),
        foto_path=row["foto_path"], expositor_id=row["expositor_id"],
        posicao_linha=row["posicao_linha"], posicao_coluna=row["posicao_coluna"])


# --- ShelfConfig CRUD ---

def insert_shelf(shelf: ShelfConfig) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO shelf_configs (nome, linhas, colunas) VALUES (?, ?, ?)",
        (shelf.nome, shelf.linhas, shelf.colunas))
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
        "UPDATE shelf_configs SET nome=?, linhas=?, colunas=? WHERE id=?",
        (shelf.nome, shelf.linhas, shelf.colunas, shelf.id))
    conn.commit()
    conn.close()


def delete_shelf(shelf_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM shelf_configs WHERE id = ?", (shelf_id,))
    conn.commit()
    conn.close()


def _row_to_shelf(row) -> ShelfConfig:
    return ShelfConfig(
        id=row["id"], nome=row["nome"],
        linhas=row["linhas"], colunas=row["colunas"])


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
