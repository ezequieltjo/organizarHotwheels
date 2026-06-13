# Vagas Bloqueadas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow marking shelf rows or individual cells as blocked so organize algorithms skip them and the visualizer shows them greyed.

**Architecture:** New `disabled_slots` SQLite table (single table, `posicao_coluna IS NULL` = row block). Storage CRUD + prune-on-shrink. Organizer functions gain optional `disabled` dict and skip blocked slots via `_is_blocked` helper. Visualizer marks blocked-empty cells grey with "✕". UI form per-shelf in Expositores tab uses multiselect for rows and cells.

**Tech Stack:** Python 3, Streamlit, Plotly, SQLite, pytest.

**Spec:** `docs/superpowers/specs/2026-06-13-vagas-bloqueadas-design.md`

---

## File Structure

**Modify:**
- `storage.py` — add `disabled_slots` table to `SCHEMA`, add 6 functions, hook `prune_disabled_slots` into `update_shelf`
- `organizers.py` — add `_is_blocked` helper, add `disabled=None` param to all 7 `organize_*` + `_fill_grid`, `_fill_wall_grid`, `_build_slot_list`, `total_slots`
- `visualizer.py` — add `disabled=None` param to `render_grid` + 2 helpers, add `_mark_disabled_for_shelf` helper
- `app.py` — load `disabled` in `refresh()`, add per-shelf form in Expositores tab, pass `disabled` to organize and render in Organizar tab

**Create:**
- `tests/test_storage_disabled.py` — CRUD + prune + cascade tests
- `tests/test_organizers_disabled.py` — `_is_blocked`, `total_slots`, fill skip tests
- `tests/test_visualizer_disabled.py` — grey marking + car-precedence tests

---

## Task 1: Storage — schema and CRUD

**Files:**
- Modify: `storage.py` (SCHEMA block + new functions after `_row_to_shelf` or near shelf CRUD)
- Test: `tests/test_storage_disabled.py` (create)

- [ ] **Step 1: Write failing tests for CRUD**

Create `tests/test_storage_disabled.py`:

```python
from models import ShelfConfig
from storage import (insert_shelf, get_disabled_slots, get_all_disabled_slots,
                     set_disabled_slot, unset_disabled_slot, clear_disabled_slots,
                     prune_disabled_slots, update_shelf, delete_shelf, get_shelf_by_id)


def _make_shelf(linhas=4, colunas=10):
    return insert_shelf(ShelfConfig(nome="P1", linhas=linhas, colunas=colunas))


def test_get_disabled_slots_empty():
    sid = _make_shelf()
    result = get_disabled_slots(sid)
    assert result == {"rows": set(), "cells": set()}


def test_set_and_get_row_block():
    sid = _make_shelf()
    set_disabled_slot(sid, 3, None)
    result = get_disabled_slots(sid)
    assert result["rows"] == {3}
    assert result["cells"] == set()


def test_set_and_get_cell_block():
    sid = _make_shelf()
    set_disabled_slot(sid, 1, 2)
    result = get_disabled_slots(sid)
    assert result["cells"] == {(1, 2)}
    assert result["rows"] == set()


def test_set_mixed_blocks():
    sid = _make_shelf()
    set_disabled_slot(sid, 0, None)
    set_disabled_slot(sid, 1, 2)
    set_disabled_slot(sid, 3, None)
    result = get_disabled_slots(sid)
    assert result["rows"] == {0, 3}
    assert result["cells"] == {(1, 2)}


def test_unset_row_block():
    sid = _make_shelf()
    set_disabled_slot(sid, 2, None)
    unset_disabled_slot(sid, 2, None)
    result = get_disabled_slots(sid)
    assert result["rows"] == set()


def test_unset_cell_block():
    sid = _make_shelf()
    set_disabled_slot(sid, 1, 3)
    unset_disabled_slot(sid, 1, 3)
    result = get_disabled_slots(sid)
    assert result["cells"] == set()


def test_clear_disabled_slots():
    sid = _make_shelf()
    set_disabled_slot(sid, 0, None)
    set_disabled_slot(sid, 1, 2)
    clear_disabled_slots(sid)
    result = get_disabled_slots(sid)
    assert result == {"rows": set(), "cells": set()}


def test_get_all_disabled_slots():
    sid1 = _make_shelf()
    sid2 = insert_shelf(ShelfConfig(nome="P2", linhas=3, colunas=8))
    set_disabled_slot(sid1, 0, None)
    set_disabled_slot(sid2, 1, 1)
    result = get_all_disabled_slots()
    assert result[sid1]["rows"] == {0}
    assert result[sid2]["cells"] == {(1, 1)}


def test_set_idempotent():
    """Inserting same row block twice doesn't duplicate."""
    sid = _make_shelf()
    set_disabled_slot(sid, 2, None)
    set_disabled_slot(sid, 2, None)
    result = get_disabled_slots(sid)
    assert result["rows"] == {2}
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_storage_disabled.py -v`
Expected: All FAIL with `ImportError: cannot import name 'get_disabled_slots'`

- [ ] **Step 3: Add table to SCHEMA**

In `storage.py`, append to the `SCHEMA` string (after `wall_config` block):

```sql
CREATE TABLE IF NOT EXISTS disabled_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shelf_id INTEGER NOT NULL,
    posicao_linha INTEGER NOT NULL,
    posicao_coluna INTEGER,
    UNIQUE(shelf_id, posicao_linha, posicao_coluna),
    FOREIGN KEY(shelf_id) REFERENCES shelf_configs(id) ON DELETE CASCADE
);
```

- [ ] **Step 4: Add CRUD functions**

In `storage.py`, after `_row_to_shelf` (around line 197), add:

```python
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
```

- [ ] **Step 5: Run tests to verify pass**

Run: `pytest tests/test_storage_disabled.py -v`
Expected: All 9 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add storage.py tests/test_storage_disabled.py
git commit -m "feat(storage): disabled_slots table + CRUD for blocked shelf slots"
```

---

## Task 2: Storage — prune on update_shelf and cascade on delete

**Files:**
- Modify: `storage.py` (`update_shelf` function ~line 177, `delete_shelf` ~line 186, `init_db` ~line 60)
- Test: `tests/test_storage_disabled.py` (extend)

- [ ] **Step 1: Write failing tests for prune and cascade**

Append to `tests/test_storage_disabled.py`:

```python
def test_prune_removes_rows_beyond_new_linhas():
    sid = _make_shelf(linhas=4, colunas=10)
    set_disabled_slot(sid, 3, None)  # row 3
    set_disabled_slot(sid, 0, None)  # row 0
    prune_disabled_slots(sid, 2, 10)  # shrink to 2 rows
    result = get_disabled_slots(sid)
    assert result["rows"] == {0}  # row 3 removed


def test_prune_removes_cells_beyond_new_dims():
    sid = _make_shelf(linhas=4, colunas=10)
    set_disabled_slot(sid, 1, 9)   # col 9 (out when colunas=5)
    set_disabled_slot(sid, 3, 2)   # row 3 (out when linhas=2)
    set_disabled_slot(sid, 1, 2)   # keep
    prune_disabled_slots(sid, 2, 5)
    result = get_disabled_slots(sid)
    assert result["cells"] == {(1, 2)}


def test_update_shelf_calls_prune():
    """update_shelf should auto-prune disabled slots when shelf shrinks."""
    from models import ShelfConfig
    from storage import insert_shelf, update_shelf, get_shelf_by_id, get_disabled_slots
    sid = insert_shelf(ShelfConfig(nome="P1", linhas=4, colunas=10))
    set_disabled_slot(sid, 3, None)
    set_disabled_slot(sid, 1, 8)
    shelf = get_shelf_by_id(sid)
    shelf.linhas = 2
    shelf.colunas = 5
    update_shelf(shelf)
    result = get_disabled_slots(sid)
    assert result["rows"] == set()       # row 3 pruned
    assert result["cells"] == set()      # col 8 pruned


def test_delete_shelf_cascades():
    """Deleting shelf removes its disabled_slots via FK cascade."""
    from models import ShelfConfig
    from storage import insert_shelf, delete_shelf, get_connection
    sid = insert_shelf(ShelfConfig(nome="P1", linhas=4, colunas=10))
    set_disabled_slot(sid, 0, None)
    set_disabled_slot(sid, 1, 2)
    delete_shelf(sid)
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM disabled_slots WHERE shelf_id=?", (sid,)).fetchone()[0]
    conn.close()
    assert count == 0
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_storage_disabled.py::test_update_shelf_calls_prune tests/test_storage_disabled.py::test_delete_shelf_cascades -v`
Expected: `test_update_shelf_calls_prune` FAILS (rows/cells still present after update). `test_delete_shelf_cascades` may PASS or FAIL depending on whether SQLite enforces FK without `PRAGMA foreign_keys=ON`.

- [ ] **Step 3: Hook prune into update_shelf**

In `storage.py`, modify `update_shelf`:

```python
def update_shelf(shelf: ShelfConfig) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE shelf_configs SET nome=?, linhas=?, colunas=?, parede_linha=?, parede_coluna=? WHERE id=?",
        (shelf.nome, shelf.linhas, shelf.colunas, shelf.parede_linha, shelf.parede_coluna, shelf.id))
    conn.commit()
    conn.close()
    prune_disabled_slots(shelf.id, shelf.linhas, shelf.colunas)
```

- [ ] **Step 4: Enable foreign keys in get_connection**

In `storage.py`, modify `get_connection` to enable FK enforcement:

```python
def get_connection():
    path = _get_path()
    if isinstance(path, Path):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
```

- [ ] **Step 5: Run all storage tests to verify pass**

Run: `pytest tests/test_storage_disabled.py tests/test_storage_shelves.py -v`
Expected: All tests PASS, no regressions.

- [ ] **Step 6: Commit**

```bash
git add storage.py tests/test_storage_disabled.py
git commit -m "feat(storage): prune disabled slots on shelf update + cascade on delete"
```

---

## Task 3: Organizer — `_is_blocked` helper and `total_slots`

**Files:**
- Modify: `organizers.py` (`_is_blocked` new, `total_slots` ~line 47)
- Test: `tests/test_organizers_disabled.py` (create)

- [ ] **Step 1: Write failing tests**

Create `tests/test_organizers_disabled.py`:

```python
from models import Car, ShelfConfig, ParedeConfig
from organizers import total_slots, _is_blocked


def make_shelves():
    return [
        ShelfConfig(id=1, nome="P1", linhas=4, colunas=10),
        ShelfConfig(id=2, nome="P2", linhas=4, colunas=10),
    ]


def test_is_blocked_returns_false_when_disabled_none():
    assert _is_blocked(1, 0, 0, None) is False


def test_is_blocked_returns_false_when_shelf_absent():
    disabled = {1: {"rows": set(), "cells": set()}}
    assert _is_blocked(99, 0, 0, disabled) is False


def test_is_blocked_row():
    disabled = {1: {"rows": {2}, "cells": set()}}
    assert _is_blocked(1, 2, 0, disabled) is True
    assert _is_blocked(1, 2, 9, disabled) is True
    assert _is_blocked(1, 1, 0, disabled) is False


def test_is_blocked_cell():
    disabled = {1: {"rows": set(), "cells": {(1, 3)}}}
    assert _is_blocked(1, 1, 3, disabled) is True
    assert _is_blocked(1, 1, 4, disabled) is False


def test_is_blocked_row_takes_precedence_over_cell():
    """If row is blocked, cell in that row is also blocked (any cell)."""
    disabled = {1: {"rows": {1}, "cells": set()}}  # row 1 blocked
    assert _is_blocked(1, 1, 5, disabled) is True


def test_total_slots_no_disabled():
    shelves = make_shelves()
    assert total_slots(shelves) == 80


def test_total_slots_subtracts_blocked_rows():
    shelves = make_shelves()
    disabled = {
        1: {"rows": {3}, "cells": set()},       # 10 blocked
        2: {"rows": {2, 3}, "cells": set()},    # 20 blocked
    }
    assert total_slots(shelves, disabled) == 80 - 30


def test_total_slots_subtracts_blocked_cells():
    shelves = make_shelves()
    disabled = {
        1: {"rows": set(), "cells": {(0, 0), (0, 1), (1, 2)}},  # 3 blocked
    }
    assert total_slots(shelves, disabled) == 80 - 3


def test_total_slots_mixed_row_and_cell_no_double_count():
    """Row blocked + cell in same row: cell should NOT be counted twice."""
    shelves = [ShelfConfig(id=1, nome="P1", linhas=2, colunas=5)]
    disabled = {
        1: {"rows": {0}, "cells": {(0, 1), (1, 2)}},  # row 0 = 5, cell (1,2) = 1 → 6
    }
    assert total_slots(shelves, disabled) == 10 - 6
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_organizers_disabled.py -v`
Expected: All FAIL with `ImportError: cannot import name '_is_blocked'`

- [ ] **Step 3: Add `_is_blocked` helper**

In `organizers.py`, after the imports (before `organize_rainbow`):

```python
def _is_blocked(shelf_id, row, col, disabled) -> bool:
    if not disabled:
        return False
    d = disabled.get(shelf_id)
    if not d:
        return False
    return row in d["rows"] or (row, col) in d["cells"]
```

- [ ] **Step 4: Update `total_slots` to subtract blocked**

Replace existing `total_slots` (around line 47):

```python
def total_slots(shelves: list[ShelfConfig], disabled: dict = None) -> int:
    total = sum(s.linhas * s.colunas for s in shelves)
    if not disabled:
        return total
    blocked = 0
    for s in shelves:
        d = disabled.get(s.id)
        if not d:
            continue
        for row in range(s.linhas):
            if row in d["rows"]:
                blocked += s.colunas
                continue
            blocked += sum(1 for col in range(s.colunas) if (row, col) in d["cells"])
    return total - blocked
```

- [ ] **Step 5: Run tests to verify pass**

Run: `pytest tests/test_organizers_disabled.py -v`
Expected: All 9 tests PASS.

- [ ] **Step 6: Run existing organizer tests to confirm no regression**

Run: `pytest tests/test_organizers.py -v`
Expected: All PASS (backward compat via `disabled=None` default).

- [ ] **Step 7: Commit**

```bash
git add organizers.py tests/test_organizers_disabled.py
git commit -m "feat(organizers): _is_blocked helper + total_slots subtracts blocked slots"
```

---

## Task 4: Organizer — fill functions skip blocked slots

**Files:**
- Modify: `organizers.py` (signatures for `organize_*`, `_dispatch_fill`, `_fill_grid`, `_fill_wall_grid`, `_build_slot_list`)
- Test: `tests/test_organizers_disabled.py` (extend)

- [ ] **Step 1: Write failing tests for fill skip**

Append to `tests/test_organizers_disabled.py`:

```python
from organizers import (_fill_grid, _fill_wall_grid, organize_rainbow,
                         organize_gradient, organize_by_brand, organize_random)
from models import Car


def _cars(n):
    return [Car(id=i+1, modelo=f"C{i}", cor_hex="#FF0000") for i in range(n)]


def test_fill_grid_skips_blocked_row():
    """Row 1 blocked → cars flow through row 0 then nothing in row 1."""
    shelves = [ShelfConfig(id=1, nome="P1", linhas=2, colunas=3)]
    disabled = {1: {"rows": {1}, "cells": set()}}
    cars = _cars(5)
    result = _fill_grid(cars, shelves, disabled=disabled)
    assert len(result) == 3  # only row 0 has 3 slots
    for car_id, (sid, r, c) in result.items():
        assert r == 0  # none in row 1


def test_fill_grid_skips_blocked_cell():
    shelves = [ShelfConfig(id=1, nome="P1", linhas=1, colunas=3)]
    disabled = {1: {"rows": set(), "cells": {(0, 1)}}}
    cars = _cars(5)
    result = _fill_grid(cars, shelves, disabled=disabled)
    assert len(result) == 2
    cols_used = {pos[2] for pos in result.values()}
    assert cols_used == {0, 2}  # col 1 skipped


def test_fill_grid_skips_blocked_multiple_shelves():
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=2),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2),
    ]
    disabled = {1: {"rows": {0}, "cells": set()}}  # all of P1 blocked
    cars = _cars(3)
    result = _fill_grid(cars, shelves, disabled=disabled)
    assert len(result) == 2  # only P2's 2 slots
    for car_id, (sid, r, c) in result.items():
        assert sid == 2


def test_fill_wall_grid_skips_blocked():
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=2, parede_linha=0, parede_coluna=0),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2, parede_linha=0, parede_coluna=1),
    ]
    wall = ParedeConfig(linhas=1, colunas=2)
    disabled = {1: {"rows": set(), "cells": {(0, 0)}}}  # P1 col 0 blocked
    cars = _cars(3)
    result = _fill_wall_grid(cars, shelves, wall, disabled=disabled)
    assert len(result) == 3
    # P1 col0 skipped, so first car goes to P1 col1
    assert result[1] == (1, 0, 1)
    assert result[2] == (2, 0, 0)
    assert result[3] == (2, 0, 1)


def test_organize_rainbow_passes_disabled_through():
    """End-to-end: organize_rainbow accepts disabled and skips blocked."""
    shelves = [ShelfConfig(id=1, nome="P1", linhas=2, colunas=3)]
    disabled = {1: {"rows": {1}, "cells": set()}}
    cars = _cars(5)
    result = organize_rainbow(cars, shelves, disabled=disabled)
    assert len(result) == 3
    for car_id, (sid, r, c) in result.items():
        assert r == 0


def test_organize_gradient_skips_blocked():
    shelves = [ShelfConfig(id=1, nome="P1", linhas=2, colunas=3)]
    disabled = {1: {"rows": {0}, "cells": set()}}  # row 0 blocked
    cars = _cars(5)
    result = organize_gradient(cars, shelves, disabled=disabled)
    assert len(result) == 3  # only row 1 available
    for car_id, (sid, r, c) in result.items():
        assert r == 1
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_organizers_disabled.py -v`
Expected: New tests FAIL with `TypeError: _fill_grid() got an unexpected keyword argument 'disabled'`

- [ ] **Step 3: Update `_fill_grid` signature and skip logic**

Replace `_fill_grid` (around line 88):

```python
def _fill_grid(cars: list[Car], shelves: list[ShelfConfig], disabled: dict = None) -> dict:
    assignment = {}
    idx = 0
    for shelf in shelves:
        for row in range(shelf.linhas):
            cols = range(shelf.colunas) if row % 2 == 0 else range(shelf.colunas - 1, -1, -1)
            for col in cols:
                if _is_blocked(shelf.id, row, col, disabled):
                    continue
                if idx >= len(cars):
                    return assignment
                assignment[cars[idx].id] = (shelf.id, row, col)
                idx += 1
    return assignment
```

- [ ] **Step 4: Update `_fill_wall_grid` signature and skip logic**

Replace `_fill_wall_grid` (around line 57):

```python
def _fill_wall_grid(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig,
                    disabled: dict = None) -> dict:
    # Build grid: wall_grid[r][c] = shelf or None
    wall_grid = [[None] * wall.colunas for _ in range(wall.linhas)]
    for shelf in shelves:
        r, c = shelf.parede_linha, shelf.parede_coluna
        if 0 <= r < wall.linhas and 0 <= c < wall.colunas:
            wall_grid[r][c] = shelf

    assignment = {}
    idx = 0
    global_row = 0
    for wall_row in range(wall.linhas):
        max_rows = max((s.linhas for s in wall_grid[wall_row] if s), default=0)
        for shelf_row in range(max_rows):
            # snake: even rows L→R, odd rows R→L
            wall_cols = range(wall.colunas) if global_row % 2 == 0 else range(wall.colunas - 1, -1, -1)
            for wall_col in wall_cols:
                shelf = wall_grid[wall_row][wall_col]
                if not shelf or shelf_row >= shelf.linhas:
                    continue
                n = shelf.colunas
                cols = range(n) if global_row % 2 == 0 else range(n - 1, -1, -1)
                for col in cols:
                    if _is_blocked(shelf.id, shelf_row, col, disabled):
                        continue
                    if idx >= len(cars):
                        return assignment
                    assignment[cars[idx].id] = (shelf.id, shelf_row, col)
                    idx += 1
            global_row += 1
    return assignment
```

- [ ] **Step 5: Update `_dispatch_fill` to pass disabled**

Replace `_dispatch_fill` (around line 51):

```python
def _dispatch_fill(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None,
                   disabled: dict = None) -> dict:
    if wall and (wall.linhas > 1 or wall.colunas > 1):
        return _fill_wall_grid(cars, shelves, wall, disabled)
    return _fill_grid(cars, shelves, disabled)
```

- [ ] **Step 6: Update all 7 `organize_*` signatures**

In `organizers.py`, modify each `organize_*` function to accept `disabled=None` and pass it to `_dispatch_fill`. Example for `organize_rainbow`:

```python
def organize_rainbow(cars: list[Car], shelves: list[ShelfConfig],
                     wall: ParedeConfig = None, disabled: dict = None) -> dict:
    sorted_cars = sorted(cars, key=lambda c: hex_para_hue(c.cor_hex))
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)
```

Apply same pattern to: `organize_by_brand`, `organize_by_fabricante`, `organize_by_year`, `organize_random`, `organize_favorites_first`. Each gains `disabled: dict = None` after `wall` and passes `disabled` to `_dispatch_fill`.

- [ ] **Step 7: Update `organize_gradient` signature**

`organize_gradient` calls `_gradient_2d_fill` directly, not `_dispatch_fill`. Replace:

```python
def organize_gradient(cars: list[Car], shelves: list[ShelfConfig],
                      wall: ParedeConfig = None, disabled: dict = None) -> dict:
    if not cars:
        return {}
    return _gradient_2d_fill(cars, shelves, wall, disabled)
```

- [ ] **Step 8: Update `_gradient_2d_fill` signature and pass disabled to `_build_slot_list`**

Modify `_gradient_2d_fill` (around line 119) to accept `disabled` and pass it to `_build_slot_list`:

```python
def _gradient_2d_fill(cars: list[Car], shelves: list[ShelfConfig],
                      wall: ParedeConfig = None, disabled: dict = None) -> dict:
    # Build slot list: (shelf_id, shelf_row, shelf_col, global_row, global_col)
    slots = _build_slot_list(shelves, wall, disabled)
    # ... rest unchanged
```

Only the first line changes (add `disabled` to `_build_slot_list` call). Leave the rest of `_gradient_2d_fill` intact.

- [ ] **Step 9: Update `_build_slot_list` signature and filter**

Modify `_build_slot_list` (around line 210) to accept `disabled` and filter at end:

```python
def _build_slot_list(shelves: list[ShelfConfig], wall: ParedeConfig = None,
                     disabled: dict = None) -> list[tuple]:
    """Returns [(shelf_id, shelf_row, shelf_col, global_row, global_col), ...]"""
    if wall and (wall.linhas > 1 or wall.colunas > 1):
        # ... existing wall branch (unchanged)
    else:
        # ... existing stacked branch (unchanged)
    if disabled:
        slots = [s for s in slots if not _is_blocked(s[0], s[1], s[2], disabled)]
    return slots
```

The existing wall and stacked branches produce `slots` locally; the filter at the very end (before `return slots`) trims blocked ones.

- [ ] **Step 10: Run disabled tests to verify pass**

Run: `pytest tests/test_organizers_disabled.py -v`
Expected: All PASS.

- [ ] **Step 11: Run full organizer test suite for regression check**

Run: `pytest tests/test_organizers.py -v`
Expected: All PASS.

- [ ] **Step 12: Commit**

```bash
git add organizers.py tests/test_organizers_disabled.py
git commit -m "feat(organizers): fill functions skip blocked slots + disabled param on organize_*"
```

---

## Task 5: Visualizer — mark blocked slots grey

**Files:**
- Modify: `visualizer.py` (signature for `render_grid`, `_render_stacked_grid`, `_render_wall_grid`; add `_mark_disabled_for_shelf` helper)
- Test: `tests/test_visualizer_disabled.py` (create)

- [ ] **Step 1: Write failing tests**

Create `tests/test_visualizer_disabled.py`:

```python
from models import Car, ShelfConfig, ParedeConfig
from visualizer import render_grid


def make_cars():
    return [Car(id=1, modelo="A", cor_hex="#FF0000")]


def make_shelf_grid():
    return [ShelfConfig(id=1, nome="P1", linhas=2, colunas=2)]


def _cell_shapes(fig):
    """Return fill shapes (excluding transparent shelf borders)."""
    return [s for s in fig.layout.shapes if s.fillcolor != "rgba(0,0,0,0)"]


def test_render_grid_accepts_disabled():
    """render_grid should accept disabled param without error."""
    disabled = {1: {"rows": {1}, "cells": set()}}
    fig = render_grid({}, make_cars(), make_shelf_grid(), disabled=disabled)
    assert fig is not None


def test_blocked_empty_cell_marked_grey():
    """Empty blocked cell should appear with #888888 fill."""
    disabled = {1: {"rows": set(), "cells": {(1, 1)}}}
    fig = render_grid({}, make_cars(), make_shelf_grid(), disabled=disabled)
    shapes = _cell_shapes(fig)
    # 2x2 = 4 cells, one (row=1, col=1) should be grey
    grey_shapes = [s for s in shapes if s.fillcolor == "#888888"]
    assert len(grey_shapes) == 1


def test_blocked_row_marks_all_cells_in_row():
    disabled = {1: {"rows": {0}, "cells": set()}}
    fig = render_grid({}, make_cars(), make_shelf_grid(), disabled=disabled)
    shapes = _cell_shapes(fig)
    grey_shapes = [s for s in shapes if s.fillcolor == "#888888"]
    assert len(grey_shapes) == 2  # 2 cols in row 0


def test_blocked_cell_with_car_keeps_car_color():
    """If a car is in a blocked slot, car color wins (no grey override)."""
    assignment = {1: (1, 1, 1)}  # car at blocked slot
    disabled = {1: {"rows": set(), "cells": {(1, 1)}}}
    fig = render_grid(assignment, make_cars(), make_shelf_grid(), disabled=disabled)
    shapes = _cell_shapes(fig)
    # Car shape should be #FF0000, not grey
    red_shapes = [s for s in shapes if s.fillcolor == "#FF0000"]
    assert len(red_shapes) == 1
    grey_shapes = [s for s in shapes if s.fillcolor == "#888888"]
    assert len(grey_shapes) == 0  # car slot not greyed


def test_disabled_none_keeps_behavior():
    """Without disabled, behavior unchanged (no grey shapes)."""
    fig = render_grid({}, make_cars(), make_shelf_grid())
    shapes = _cell_shapes(fig)
    grey_shapes = [s for s in shapes if s.fillcolor == "#888888"]
    assert len(grey_shapes) == 0


def test_wall_grid_marks_blocked():
    """Wall grid path also marks blocked cells."""
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=2, parede_linha=0, parede_coluna=0),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2, parede_linha=0, parede_coluna=1),
    ]
    wall = ParedeConfig(linhas=1, colunas=2)
    disabled = {2: {"rows": set(), "cells": {(0, 0)}}}  # P2 col 0 blocked
    fig = render_grid({}, make_cars(), shelves, wall, disabled=disabled)
    shapes = _cell_shapes(fig)
    grey_shapes = [s for s in shapes if s.fillcolor == "#888888"]
    assert len(grey_shapes) == 1
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_visualizer_disabled.py -v`
Expected: All FAIL with `TypeError: render_grid() got an unexpected keyword argument 'disabled'`

- [ ] **Step 3: Add `_mark_disabled_for_shelf` helper**

In `visualizer.py`, after `CELL_H = 9`:

```python
def _mark_disabled_for_shelf(disabled, shelf_id, fill_colors, texts, g_row_offset):
    """Grey out blocked-empty cells. Cars (non-empty text) are NOT overridden."""
    if not disabled:
        return
    d = disabled.get(shelf_id)
    if not d:
        return
    for r in d["rows"]:
        target_row = g_row_offset + r
        if target_row >= len(fill_colors):
            continue
        for c in range(len(fill_colors[target_row])):
            if texts[target_row][c] == "":
                fill_colors[target_row][c] = "#888888"
                texts[target_row][c] = "✕"
    for (r, c) in d["cells"]:
        target_row = g_row_offset + r
        if target_row >= len(fill_colors) or c >= len(fill_colors[target_row]):
            continue
        if texts[target_row][c] == "":
            fill_colors[target_row][c] = "#888888"
            texts[target_row][c] = "✕"
```

- [ ] **Step 4: Update `render_grid` signature**

Replace `render_grid` (line 8):

```python
def render_grid(assignment: dict, cars: list[Car], shelves: list[ShelfConfig],
                wall: ParedeConfig = None, disabled: dict = None) -> go.Figure:
    """Render grid visual. assignment: {car_id: (shelf_id, row, col)}"""
    if wall and (wall.linhas > 1 or wall.colunas > 1):
        return _render_wall_grid(assignment, cars, shelves, wall, disabled)
    return _render_stacked_grid(assignment, cars, shelves, disabled)
```

- [ ] **Step 5: Update `_render_stacked_grid` signature and call `_mark_disabled_for_shelf`**

Modify `_render_stacked_grid` (line 16):

```python
def _render_stacked_grid(assignment: dict, cars: list[Car], shelves: list[ShelfConfig],
                         disabled: dict = None) -> go.Figure:
    car_map = {c.id: c for c in cars}
    shelf_map = {s.id: s for s in shelves}

    max_col = max((s.colunas for s in shelves), default=0)
    total_rows = sum(s.linhas for s in shelves)

    colors = [["#F0F0F0"] * max_col for _ in range(total_rows)]
    texts = [[""] * max_col for _ in range(total_rows)]
    border_colors = [["#CCCCCC"] * max_col for _ in range(total_rows)]

    row_offset = 0
    for shelf in shelves:
        for s_row in range(shelf.linhas):
            g_row = row_offset + s_row
            for s_col in range(shelf.colunas):
                border_colors[g_row][s_col] = "#999999"
        row_offset += shelf.linhas

    for car_id, (shelf_id, s_row, s_col) in assignment.items():
        car = car_map.get(car_id)
        if not car:
            continue
        shelf = shelf_map.get(shelf_id)
        if not shelf:
            continue
        shelf_idx = shelves.index(shelf)
        g_row = sum(s.linhas for s in shelves[:shelf_idx]) + s_row
        colors[g_row][s_col] = car.cor_hex
        texts[g_row][s_col] = _car_label(car)
        if car.favorito:
            border_colors[g_row][s_col] = "#FFD700"

    # Mark blocked-empty cells grey
    row_offset = 0
    for shelf in shelves:
        _mark_disabled_for_shelf(disabled, shelf.id, colors, texts, row_offset)
        row_offset += shelf.linhas

    # ... rest of function unchanged (heatmap + shapes + layout)
```

Only insert the new `row_offset` loop AFTER the car-placement loop and BEFORE the `fig = go.Figure(...)` line. Rest of function unchanged.

- [ ] **Step 6: Update `_render_wall_grid` signature and call helper**

Modify `_render_wall_grid` (line 95):

```python
def _render_wall_grid(assignment: dict, cars: list[Car], shelves: list[ShelfConfig],
                      wall: ParedeConfig, disabled: dict = None) -> go.Figure:
    # ... existing wall grid construction up to and including the car-placement loop ...

    # AFTER the car-placement loop (after the "Place cars" block), BEFORE the
    # `fig = go.Figure(...)` line, add:
    for wall_row in range(wall.linhas):
        for wall_col in range(wall.colunas):
            shelf = wall_grid[wall_row][wall_col]
            if not shelf:
                continue
            _mark_disabled_for_shelf(disabled, shelf.id, grid_colors, grid_texts,
                                     row_offsets[wall_row])
```

Insert this loop between the "Place cars" loop and the `fig = go.Figure(...)` line. Rest unchanged.

- [ ] **Step 7: Run visualizer disabled tests to verify pass**

Run: `pytest tests/test_visualizer_disabled.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 8: Run existing visualizer tests for regression**

Run: `pytest tests/test_visualizer.py -v`
Expected: All PASS.

- [ ] **Step 9: Commit**

```bash
git add visualizer.py tests/test_visualizer_disabled.py
git commit -m "feat(visualizer): grey + ✕ marker on blocked-empty cells"
```

---

## Task 6: App — load disabled state and integrate in Organizar tab

**Files:**
- Modify: `app.py` (`refresh()` ~line 35, imports ~line 6, Organizar tab ~line 395)

- [ ] **Step 1: Update imports**

In `app.py`, modify the `from storage import (...)` block to include `get_all_disabled_slots`:

```python
from storage import (init_db, insert_car, get_all_cars, update_car, delete_car,
                     get_all_disabled_slots,
                     # ... existing imports ...
```

Add `get_all_disabled_slots` to the existing import list.

- [ ] **Step 2: Load disabled in `refresh()`**

Modify `refresh()` (line 35):

```python
def refresh():
    st.session_state.cars = get_all_cars()
    st.session_state.shelves = get_all_shelves()
    st.session_state.wall = get_wall_config()
    st.session_state.disabled = get_all_disabled_slots()
```

- [ ] **Step 3: Update Organizar tab to use disabled**

In `app.py` Organizar tab (around line 394-403), change:

```python
    else:
        slots = total_slots(shelves)
        if len(cars) > slots:
            st.warning(f"{len(cars)} carros mas apenas {slots} vagas. Alguns não serão posicionados.")

        modo = st.selectbox("Modo de organização", list(ORGANIZERS.keys()))

        if st.button("Gerar organização"):
            func = ORGANIZERS[modo]
            assignment = func(cars, shelves, wall)
            st.session_state.assignment = assignment
            st.rerun()

        if "assignment" in st.session_state and st.session_state.assignment:
            assignment = st.session_state.assignment
            fig = render_grid(assignment, cars, shelves, wall)
```

to:

```python
    else:
        disabled = st.session_state.disabled
        slots = total_slots(shelves, disabled)
        if len(cars) > slots:
            st.warning(f"{len(cars)} carros mas apenas {slots} vagas (após bloqueios). Alguns não serão posicionados.")

        modo = st.selectbox("Modo de organização", list(ORGANIZERS.keys()))

        if st.button("Gerar organização"):
            func = ORGANIZERS[modo]
            assignment = func(cars, shelves, wall, disabled)
            st.session_state.assignment = assignment
            st.rerun()

        if "assignment" in st.session_state and st.session_state.assignment:
            assignment = st.session_state.assignment
            fig = render_grid(assignment, cars, shelves, wall, disabled)
```

- [ ] **Step 4: Manual smoke test**

Run: `streamlit run app.py`
Verify:
1. App loads without error.
2. Add 2 shelves (4×10 each) in Expositores tab.
3. Go to Organizar tab. With 0 cars, no warning.
4. Add 5 cars in Coleção tab.
5. Go to Organizar tab → "Gerar organização" → cars fill all 5 slots starting from row 0.
6. Without blocked slots, behavior is identical to before (no grey cells).

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat(app): load disabled slots and pass to organize + render"
```

---

## Task 7: App — per-shelf block form in Expositores tab

**Files:**
- Modify: `app.py` (Expositores tab, expander block ~line 345)

- [ ] **Step 1: Add imports for CRUD**

In `app.py` `from storage import (...)` block, add: `get_disabled_slots, set_disabled_slot, clear_disabled_slots`.

- [ ] **Step 2: Add block form inside shelf expander**

In `app.py`, find the expander block in the Expositores tab (around line 345). The current structure is:

```python
    wall = st.session_state.wall
    for shelf in st.session_state.shelves:
        with st.expander(f"{shelf.nome} ({shelf.linhas}x{shelf.colunas})"):
            with st.form(f"shelf_form_{shelf.id}"):
                # ... existing form ...
```

Modify to add block UI after the form (inside the expander but outside the form):

```python
    wall = st.session_state.wall
    for shelf in st.session_state.shelves:
        with st.expander(f"{shelf.nome} ({shelf.linhas}x{shelf.colunas})"):
            with st.form(f"shelf_form_{shelf.id}"):
                # ... existing form unchanged ...

            # Vagas bloqueadas
            current = get_disabled_slots(shelf.id)
            st.markdown("**Vagas bloqueadas**")

            row_options = list(range(shelf.linhas))
            selected_rows = st.multiselect(
                "Linhas bloqueadas (inteiras)",
                options=row_options,
                default=sorted(current["rows"]),
                format_func=lambda r: f"Linha {r+1}",
                key=f"block_rows_{shelf.id}",
            )

            cell_options = [(r, c) for r in range(shelf.linhas)
                            for c in range(shelf.colunas)]
            selected_cells = st.multiselect(
                "Células individuais",
                options=cell_options,
                default=[rc for rc in sorted(current["cells"])
                         if rc[0] not in current["rows"]],
                format_func=lambda rc: f"(L{rc[0]+1}, C{rc[1]+1})",
                key=f"block_cells_{shelf.id}",
            )

            if st.button("Salvar bloqueio", key=f"save_block_{shelf.id}"):
                clear_disabled_slots(shelf.id)
                for r in selected_rows:
                    set_disabled_slot(shelf.id, r, None)
                for (r, c) in selected_cells:
                    if r not in selected_rows:
                        set_disabled_slot(shelf.id, r, c)
                refresh()
                st.rerun()
```

- [ ] **Step 3: Manual smoke test — full flow**

Run: `streamlit run app.py`
Verify:
1. Add shelf "P1" 4×10.
2. Expand P1 → see "Vagas bloqueadas" section.
3. Select "Linha 4" in rows multiselect → click "Salvar bloqueio".
4. Refresh: "Linha 4" still selected (persisted).
5. Add 35 cars in Coleção.
6. Go to Organizar → "Gerar organização".
7. Preview: row 4 shows grey cells with "✕" markers, cars fill rows 0-3 only.
8. Click "Aplicar posições" → DB updated; cars positioned only in rows 0-3.
9. Add second shelf "P2" 4×10, block rows 2-4 (3 rows = 30 cells).
10. Re-organize: cars distributed across P1 (40 slots) and P2 (10 slots).
11. Total slots warning if cars > available.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat(app): per-shelf form to block rows and cells in Expositores tab"
```

---

## Task 8: Final regression sweep

**Files:**
- All test files.

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS (existing + new disabled tests).

- [ ] **Step 2: Verify wall grid integration with disabled**

Run: `streamlit run app.py`
Wall path:
1. Set wall to 1×2 (1 row, 2 cols).
2. Place P1 at (0,0) 2×2, P2 at (0,1) 2×2.
3. Block P1 (0,0) cell.
4. Add 3 cars.
5. Organize → first car should go to P1 (0,1), then P2 cells.
6. Preview should show grey "✕" at P1 (0,0).

- [ ] **Step 3: Verify prune on shrink**

Run: `streamlit run app.py`
1. Add shelf P1 4×10, block row 3.
2. Edit P1 → reduce linhas to 2 → save.
3. Expand P1 → "Linha 3" no longer appears in row options (out of range); block state for row 3 pruned from DB.
4. Increase linhas back to 4 → row 3 reappears, no longer blocked.

- [ ] **Step 4: Verify cascade on delete**

1. Add shelf P1, block some rows.
2. Delete P1 via form.
3. Inspect DB: `SELECT * FROM disabled_slots` should return no rows for that shelf_id.

- [ ] **Step 5: Final commit (if any docs/changelog needed)**

If all tests pass and manual checks pass, the feature is complete. No additional commit unless documentation updates are needed.

```bash
git status
```

Expected: clean working tree (or only unrelated changes).

---

## Summary

After all tasks complete:

- New `disabled_slots` SQLite table tracks blocked rows and cells per shelf.
- `prune_disabled_slots` runs automatically on `update_shelf`.
- Cascade delete cleans up when shelf removed.
- All 7 `organize_*` functions accept `disabled` param and skip blocked slots.
- `total_slots` reports effective capacity.
- Visualizer marks blocked-empty cells grey with "✕"; cars in blocked slots remain visible until next organize.
- Per-shelf multiselect form in Expositores tab lets user pick rows and cells to block.
- Full backward compatibility: empty `disabled_slots` table = current behavior.
