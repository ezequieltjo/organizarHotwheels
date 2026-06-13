from models import Car, ShelfConfig, ParedeConfig
from organizers import (total_slots, _is_blocked, _fill_grid, _fill_wall_grid,
                        organize_rainbow, organize_gradient, organize_by_brand,
                        organize_random)


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
        1: {"rows": {0}, "cells": {(0, 1), (1, 2)}},  # row 0 = 5, cell (1,2) = 1 -> 6
    }
    assert total_slots(shelves, disabled) == 10 - 6


# --- Helper for new tests ---

def _cars(n):
    return [Car(id=i+1, modelo=f"C{i}", cor_hex="#FF0000") for i in range(n)]


# --- Fill skip tests ---


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
