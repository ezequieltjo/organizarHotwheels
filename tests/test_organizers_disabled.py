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
        1: {"rows": {0}, "cells": {(0, 1), (1, 2)}},  # row 0 = 5, cell (1,2) = 1 -> 6
    }
    assert total_slots(shelves, disabled) == 10 - 6
