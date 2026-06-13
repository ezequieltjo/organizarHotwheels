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
