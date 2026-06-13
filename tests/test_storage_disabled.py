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
