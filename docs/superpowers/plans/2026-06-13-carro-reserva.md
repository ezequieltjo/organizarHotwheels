# Carro Reserva Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add boolean `reserva` flag to cars. Reserved cars stay in collection but skipped by organize algorithm. `set_reserva(True)` clears existing position atomically.

**Architecture:** New `reserva` column in `cars` table (INTEGER NOT NULL DEFAULT 0, migrated via ALTER). Storage gains `set_reserva` function for atomic toggle + position clear. Organizer `_filter_reserva` helper applied at top of every `organize_*`. UI: checkbox in add/edit forms + toggle button in list with 📦 marker.

**Tech Stack:** Python 3, Streamlit, SQLite, Plotly, pytest.

**Spec:** `docs/superpowers/specs/2026-06-13-carro-reserva-design.md`

---

## File Structure

**Modify:**
- `models.py` — add `reserva: bool = False` to Car dataclass
- `storage.py` — add `reserva` to SCHEMA, init_db migration, insert_car, update_car, _row_to_car; new `set_reserva` function
- `organizers.py` — add `_filter_reserva` helper; call at top of all 7 `organize_*` + `_gradient_2d_fill`
- `app.py` — checkbox in add/edit forms, toggle button + 📦 marker in list, warning count uses non-reserva cars

**Create:**
- `tests/test_storage_reserva.py` — set_reserva + migration tests
- `tests/test_organizers_reserva.py` — _filter_reserva + organize skip tests

---

## Task 1: Models + Storage — schema, migration, CRUD

**Files:**
- Modify: `models.py:6-21` (Car dataclass)
- Modify: `storage.py:8-39` (SCHEMA), `storage.py:60-87` (init_db), `storage.py:90-102` (insert_car), `storage.py:119-129` (update_car), `storage.py:139-147` (_row_to_car); add new function after `delete_car`
- Test: `tests/test_storage_reserva.py` (create)

- [ ] **Step 1: Write failing tests**

Create `tests/test_storage_reserva.py`:

```python
from models import Car, ShelfConfig
from storage import (insert_car, update_car, get_car_by_id, set_reserva,
                     insert_shelf, apply_positions)


def test_insert_car_with_reserva_default_false():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    car = get_car_by_id(cid)
    assert car.reserva is False


def test_insert_car_with_reserva_true():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000", reserva=True))
    car = get_car_by_id(cid)
    assert car.reserva is True


def test_update_car_preserves_reserva():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000", reserva=True))
    car = get_car_by_id(cid)
    car.modelo = "B"
    update_car(car)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is True
    assert refreshed.modelo == "B"


def test_update_car_toggles_reserva():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000", reserva=False))
    car = get_car_by_id(cid)
    car.reserva = True
    update_car(car)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is True


def test_set_reserva_true_clears_position():
    """set_reserva(True) on positioned car clears expositor_id and position."""
    sid = insert_shelf(ShelfConfig(nome="P1", linhas=2, colunas=2))
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    apply_positions({cid: (sid, 0, 0)})
    car = get_car_by_id(cid)
    assert car.expositor_id == sid  # sanity check
    set_reserva(cid, True)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is True
    assert refreshed.expositor_id is None
    assert refreshed.posicao_linha is None
    assert refreshed.posicao_coluna is None


def test_set_reserva_false_keeps_null_position():
    """set_reserva(False) does NOT re-position (position stays NULL)."""
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    set_reserva(cid, True)
    set_reserva(cid, False)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is False
    assert refreshed.expositor_id is None


def test_set_reserva_idempotent():
    """Calling set_reserva twice with same value is safe."""
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    set_reserva(cid, True)
    set_reserva(cid, True)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is True


def test_set_reserva_false_when_already_false():
    cid = insert_car(Car(modelo="A", cor_hex="#FF0000"))
    set_reserva(cid, False)
    refreshed = get_car_by_id(cid)
    assert refreshed.reserva is False
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_storage_reserva.py -v`
Expected: All FAIL with `AttributeError: 'Car' object has no attribute 'reserva'` or `ImportError: cannot import name 'set_reserva'`

- [ ] **Step 3: Add `reserva` field to Car dataclass**

In `models.py`, add `reserva: bool = False` after `favorito` (line 15):

```python
@dataclass
class Car:
    id: Optional[int] = None
    modelo: str = ""
    marca: str = ""
    fabricante: str = ""
    ano: int = 0
    cor: str = ""
    cor_hex: str = ""
    serie_tipo: str = ""
    favorito: bool = False
    reserva: bool = False
    foto_path: str = ""
    expositor_id: Optional[int] = None
    posicao_linha: Optional[int] = None
    posicao_coluna: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
```

- [ ] **Step 4: Add column to SCHEMA**

In `storage.py`, modify the `cars` CREATE TABLE block in SCHEMA (around line 9):

```sql
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
```

- [ ] **Step 5: Add migration in init_db**

In `storage.py`, in `init_db()` (around line 64, after the `fabricante` migration block), add:

```python
    if "reserva" not in cols:
        conn.execute("ALTER TABLE cars ADD COLUMN reserva INTEGER NOT NULL DEFAULT 0")
```

- [ ] **Step 6: Update insert_car**

Replace `insert_car` (around line 90):

```python
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
```

- [ ] **Step 7: Update update_car**

Replace `update_car` (around line 119):

```python
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
```

- [ ] **Step 8: Update _row_to_car**

Replace `_row_to_car` (around line 139):

```python
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
```

- [ ] **Step 9: Add set_reserva function**

In `storage.py`, after `delete_car` (around line 136), add:

```python
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
```

- [ ] **Step 10: Run tests to verify pass**

Run: `pytest tests/test_storage_reserva.py -v`
Expected: All 8 tests PASS.

- [ ] **Step 11: Run full storage test suite for regressions**

Run: `pytest tests/test_storage.py tests/test_storage_shelves.py tests/test_storage_disabled.py -v`
Expected: All PASS (no regressions).

- [ ] **Step 12: Commit**

```bash
git add models.py storage.py tests/test_storage_reserva.py
git commit -m "feat(storage): reserva column + set_reserva atomic toggle"
```

---

## Task 2: Organizer — filter reservas before organize

**Files:**
- Modify: `organizers.py` (add `_filter_reserva`, modify 7 `organize_*` + `_gradient_2d_fill`)
- Test: `tests/test_organizers_reserva.py` (create)

- [ ] **Step 1: Write failing tests**

Create `tests/test_organizers_reserva.py`:

```python
from models import Car, ShelfConfig, ParedeConfig
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        organize_favorites_first, _filter_reserva)


def make_cars():
    return [
        Car(id=1, modelo="A", cor_hex="#FF0000", cor="vermelho", marca="Chevrolet",
            fabricante="Hot Wheels", ano=2023, favorito=False),
        Car(id=2, modelo="B", cor_hex="#0000FF", cor="azul", marca="Ford",
            fabricante="Matchbox", ano=2022, favorito=True),
        Car(id=3, modelo="C", cor_hex="#00FF00", cor="verde", marca="Chevrolet",
            fabricante="Hot Wheels", ano=2024, favorito=False),
    ]


def make_shelves():
    return [ShelfConfig(id=1, nome="P1", linhas=2, colunas=2)]


def test_filter_reserva_excludes_reserved():
    cars = make_cars()
    cars[1].reserva = True  # id=2 reserved
    filtered = _filter_reserva(cars)
    assert len(filtered) == 2
    assert all(c.reserva is False for c in filtered)
    assert {c.id for c in filtered} == {1, 3}


def test_filter_reserva_empty_when_all_reserved():
    cars = make_cars()
    for c in cars:
        c.reserva = True
    filtered = _filter_reserva(cars)
    assert filtered == []


def test_filter_reserva_keeps_all_when_none_reserved():
    cars = make_cars()
    filtered = _filter_reserva(cars)
    assert len(filtered) == 3


def test_organize_rainbow_skips_reserva():
    cars = make_cars()
    cars[0].reserva = True  # id=1 (vermelho) reserved
    result = organize_rainbow(cars, make_shelves())
    assert len(result) == 2
    assert 1 not in result  # reservado não posiciona
    assert set(result.keys()) == {2, 3}


def test_organize_gradient_skips_reserva():
    cars = make_cars()
    cars[0].reserva = True
    result = organize_gradient(cars, make_shelves())
    assert len(result) == 2
    assert 1 not in result


def test_organize_by_brand_skips_reserva():
    cars = make_cars()
    cars[2].reserva = True  # id=3 (Chevrolet verde)
    result = organize_by_brand(cars, make_shelves())
    assert len(result) == 2
    assert 3 not in result


def test_organize_random_skips_reserva():
    cars = make_cars()
    cars[1].reserva = True
    result = organize_random(cars, make_shelves())
    assert len(result) == 2
    assert 2 not in result


def test_organize_favorites_first_skips_reserva():
    """Favorito + reserva → reserva ganha, não posiciona."""
    cars = make_cars()
    cars[1].reserva = True  # id=2 era favorito
    cars[1].favorito = True
    result = organize_favorites_first(cars, make_shelves())
    assert len(result) == 2
    assert 2 not in result  # reservado (mesmo favorito) não posiciona


def test_organize_all_reservas_returns_empty():
    cars = make_cars()
    for c in cars:
        c.reserva = True
    result = organize_rainbow(cars, make_shelves())
    assert result == {}


def test_organize_reserva_with_disabled_integration():
    """Reserva filter + disabled slots: ambos aplicados juntos."""
    shelves = [ShelfConfig(id=1, nome="P1", linhas=2, colunas=2)]
    disabled = {1: {"rows": {0}, "cells": set()}}  # row 0 bloqueada
    cars = make_cars()
    cars[0].reserva = True  # id=1 reservado
    result = organize_rainbow(cars, shelves, disabled=disabled)
    # 3 cars - 1 reserva = 2; row 0 bloqueada → row 1 tem 2 slots
    assert len(result) == 2
    assert 1 not in result
    for car_id, (sid, r, c) in result.items():
        assert r == 1  # todos na row 1 (row 0 bloqueada)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_organizers_reserva.py -v`
Expected: All FAIL with `ImportError: cannot import name '_filter_reserva'`

- [ ] **Step 3: Add `_filter_reserva` helper**

In `organizers.py`, after `_is_blocked` helper (around line 16), add:

```python
def _filter_reserva(cars: list[Car]) -> list[Car]:
    """Exclui carros marcados como reserva da organização."""
    return [c for c in cars if not c.reserva]
```

- [ ] **Step 4: Apply filter to all 7 organize_* functions**

Modify each of the 7 `organize_*` functions to call `_filter_reserva` at the top.

For `organize_rainbow`:

```python
def organize_rainbow(cars: list[Car], shelves: list[ShelfConfig],
                     wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    sorted_cars = sorted(cars, key=lambda c: hex_para_hue(c.cor_hex))
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)
```

For `organize_by_brand`:

```python
def organize_by_brand(cars: list[Car], shelves: list[ShelfConfig],
                      wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    sorted_cars = sorted(cars, key=lambda c: (c.marca, c.cor))
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)
```

For `organize_by_fabricante`:

```python
def organize_by_fabricante(cars: list[Car], shelves: list[ShelfConfig],
                           wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    sorted_cars = sorted(cars, key=lambda c: (c.fabricante, c.cor))
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)
```

For `organize_by_year`:

```python
def organize_by_year(cars: list[Car], shelves: list[ShelfConfig],
                     wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    sorted_cars = sorted(cars, key=lambda c: c.ano)
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)
```

For `organize_random`:

```python
def organize_random(cars: list[Car], shelves: list[ShelfConfig],
                    wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    shuffled = list(cars)
    random.shuffle(shuffled)
    return _dispatch_fill(shuffled, shelves, wall, disabled)
```

For `organize_favorites_first`:

```python
def organize_favorites_first(cars: list[Car], shelves: list[ShelfConfig],
                             wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    favs = [c for c in cars if c.favorito]
    rest = [c for c in cars if not c.favorito]
    return _dispatch_fill(favs + rest, shelves, wall, disabled)
```

For `organize_gradient`:

```python
def organize_gradient(cars: list[Car], shelves: list[ShelfConfig],
                      wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    if not cars:
        return {}
    return _gradient_2d_fill(cars, shelves, wall, disabled)
```

- [ ] **Step 5: Run tests to verify pass**

Run: `pytest tests/test_organizers_reserva.py -v`
Expected: All 10 tests PASS.

- [ ] **Step 6: Run full organizer test suite for regressions**

Run: `pytest tests/test_organizers.py tests/test_organizers_disabled.py tests/test_organizers_reserva.py -v`
Expected: 10 new reserva tests pass. Existing organizer tests pass at same rate (15 pass + 3 pre-existing fail for snake-ordering, 15 disabled tests pass).

- [ ] **Step 7: Commit**

```bash
git add organizers.py tests/test_organizers_reserva.py
git commit -m "feat(organizers): _filter_reserva skips reserved cars in organize_*"
```

---

## Task 3: App — checkbox forms, toggle list, warning count

**Files:**
- Modify: `app.py` (imports, Coleção tab list ~line 294, add/edit forms ~lines 119/203, Organizar warning ~line 398)

- [ ] **Step 1: Add set_reserva to imports**

In `app.py`, modify `from storage import (...)` block (around line 6) to include `set_reserva`:

```python
from storage import (init_db, insert_car, get_all_cars, update_car, delete_car,
                     insert_shelf, get_all_shelves, update_shelf, delete_shelf,
                     clear_positions, apply_positions, get_wall_config, save_wall_config,
                     get_all_disabled_slots, get_disabled_slots, replace_disabled_slots,
                     set_reserva)
```

- [ ] **Step 2: Add 📦 toggle button in Coleção list**

In `app.py`, find the Coleção tab list rendering (around line 290-300). The current structure uses toggle for favorito. Add reserva toggle alongside.

Find this block (around lines 294-299):

```python
                    fav = "★ " if car.favorito else ""
                    # ... existing display ...
                    if st.button("★" if car.favorito else "☆", key=f"fav_{car.id}"):
                        car.favorito = not car.favorito
                        update_car(car)
                        refresh()
                        st.rerun()
```

Add reserve toggle right after the favorite button:

```python
                    if st.button("📦" if car.reserva else "·", key=f"reserva_{car.id}",
                                 help="Marcar reserva (não posicionar)"):
                        set_reserva(car.id, not car.reserva)
                        refresh()
                        st.rerun()
```

Also add the 📦 marker in the displayed label. Find where the car label/name is rendered (typically in a `st.write` or column) and prefix with `"📦 " if car.reserva else ""`. For example, if current label is `f"{fav}{car.modelo}"`, change to `f"{reserva_marker}{fav}{car.modelo}"` where `reserva_marker = "📦 " if car.reserva else ""`.

Note: Read the existing list rendering code carefully to identify the exact line where labels are constructed. The favorite marker pattern is the template — add the reserva marker at the same place.

- [ ] **Step 3: Add checkbox in add_car form**

In `app.py`, find the `add_car` form (around line 203). Add a checkbox for reserva inside the form. Place it next to the existing favorite checkbox (if any) or as a standalone field:

```python
with st.form("add_car"):
    # ... existing fields (modelo, marca, fabricante, ano, cor, etc.) ...
    favorito_add = st.checkbox("Favorito", value=False)
    reserva_add = st.checkbox("Reserva (não posicionar em expositor)", value=False)
    # ... foto_path, color picker, etc. ...
    if form_submit_button("Adicionar"):
        new_car = Car(
            modelo=modelo,
            # ... other fields ...
            favorito=favorito_add,
            reserva=reserva_add,
            cor_hex=cor_picker.upper(),
        )
        # ... insert_car logic ...
```

Find the actual structure of the add form in `app.py` to place the checkbox consistently with the existing favorito field.

- [ ] **Step 4: Add checkbox in edit_car form**

In `app.py`, find the `edit_car` form (around line 119). Similar pattern:

```python
with st.form("edit_car"):
    # ... existing fields pre-populated from editing_car ...
    favorito_edit = st.checkbox("Favorito", value=editing_car.favorito)
    reserva_edit = st.checkbox("Reserva (não posicionar em expositor)", value=editing_car.reserva)
    # ... other fields ...
    if form_submit_button("Salvar"):
        editing_car.favorito = favorito_edit
        editing_car.reserva = reserva_edit
        # ... other field assignments ...
        if reserva_edit and editing_car.expositor_id is not None:
            update_car(editing_car)
            set_reserva(editing_car.id, True)  # limpa posição
        else:
            update_car(editing_car)
        # ... refresh/rerun ...
```

The handler checks if reserva was just turned on AND the car had a position — if so, call `set_reserva(True)` after `update_car` to atomically clear the position. Otherwise just `update_car`.

- [ ] **Step 5: Update Organizar warning count**

In `app.py`, find the warning block in Organizar tab (around line 397-400). Current code:

```python
        disabled = st.session_state.disabled
        slots = total_slots(shelves, disabled)
        if len(cars) > slots:
            st.warning(f"{len(cars)} carros mas apenas {slots} vagas (após bloqueios). Alguns não serão posicionados.")
```

Change to filter reservas:

```python
        disabled = st.session_state.disabled
        active_cars = [c for c in cars if not c.reserva]
        slots = total_slots(shelves, disabled)
        if len(active_cars) > slots:
            n_reservas = len(cars) - len(active_cars)
            reserva_note = f" ({n_reservas} reservas)" if n_reservas > 0 else ""
            st.warning(f"{len(active_cars)} carros ativos mas apenas {slots} vagas{reserva_note}. "
                       f"Alguns não serão posicionados.")
```

- [ ] **Step 6: Smoke test — syntax + import**

```bash
cd D:\Code\organizarHotwheels
python -c "import ast; ast.parse(open('app.py', encoding='utf-8').read())"
```

Expected: no output (syntax OK).

- [ ] **Step 7: Run full test suite for regressions**

```bash
pytest tests/ -v
```

Expected: all previous tests pass at same rate (95 pass + 3 pre-existing fail). New reserva tests (18 total: 8 storage + 10 organizer) all pass.

- [ ] **Step 8: Commit**

```bash
git add app.py
git commit -m "feat(app): reserva checkbox in forms + toggle button + warning count"
```

---

## Task 4: Final regression sweep

**Files:** All test files.

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v
```

Expected: 113 pass + 3 pre-existing fail (snake-ordering, unrelated).

- [ ] **Step 2: Manual smoke test — full flow**

Run `streamlit run app.py` and verify:

1. Add a car in Coleção → checkbox "Reserva" present in form.
2. Add another car with "Reserva" checked.
3. Both cars appear in list. Reserved car has 📦 marker.
4. Click 📦 toggle on a non-reserved car → it becomes 📦 (reserva).
5. Click · toggle on a reserved car → it loses 📦.
6. Add shelf 4×4 in Expositores.
7. Go to Organizar → "Gerar organização".
8. Reserved cars do NOT appear in the assignment grid.
9. Reserved cars still appear in the Coleção list.
10. Position a car manually (or via organize + apply). Then mark it as reserva via toggle. Verify its `expositor_id` becomes NULL (it disappears from Expositores grid preview on next render).
11. Warning count: if reservas exist, message includes "(N reservas)" suffix.

- [ ] **Step 3: Verify migration on existing DB**

The existing `collection.db` has 162 cars without `reserva` column. Verify `init_db` adds it on next launch:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('db/collection.db')
cols = [r[1] for r in conn.execute('PRAGMA table_info(cars)').fetchall()]
print('reserva' in cols)
"
```

Run the app once (or just `python -c "from storage import init_db; init_db()"`), then re-check: `'reserva' in cols` should be `True` and all existing cars have `reserva=0`.

---

## Summary

After all tasks complete:

- `cars` table has new `reserva` column (INTEGER NOT NULL DEFAULT 0)
- Migration auto-applies on `init_db` for existing DBs
- `set_reserva(car_id, True)` atomically clears position
- All 7 `organize_*` functions skip reserved cars via `_filter_reserva`
- `_gradient_2d_fill` also skips reservas (via organize_gradient)
- Coleção list shows 📦 marker for reservas + toggle button
- Add/edit forms have reserva checkbox
- Warning count in Organizar tab excludes reservas and notes "(N reservas)"
- Importer (`importer.py`) needs no change (Car dataclass default `reserva=False`)
- Visualizer needs no change (reserva cars have no position, already excluded)
- Full backward compatibility: empty reserva column = current behavior
