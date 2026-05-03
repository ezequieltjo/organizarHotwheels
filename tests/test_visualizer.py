from models import Car, ShelfConfig
from visualizer import render_grid


def make_assignment():
    return {1: (1, 0, 0), 2: (1, 0, 1), 3: (1, 1, 0)}


def make_cars():
    return [
        Car(id=1, modelo="Corvette", cor_hex="#FF0000", favorito=True),
        Car(id=2, modelo="Mustang", cor_hex="#0000FF", favorito=False),
        Car(id=3, modelo="Camaro", cor_hex="#00FF00", favorito=False),
    ]


def make_shelves():
    return [ShelfConfig(id=1, nome="P1", linhas=2, colunas=2)]


def test_render_grid_returns_figure():
    fig = render_grid(make_assignment(), make_cars(), make_shelves())
    assert fig is not None
    assert len(fig.layout.shapes) == 4  # 2x2 = 4 cells


def test_render_grid_shape_colors():
    fig = render_grid(make_assignment(), make_cars(), make_shelves())
    shapes = fig.layout.shapes
    assert shapes[0].fillcolor == "#FF0000"  # car 1
    assert shapes[1].fillcolor == "#0000FF"  # car 2
    assert shapes[2].fillcolor == "#00FF00"  # car 3
    assert shapes[3].fillcolor == "#F0F0F0"  # empty


def test_render_grid_favorite_border():
    fig = render_grid(make_assignment(), make_cars(), make_shelves())
    assert fig.layout.shapes[0].line.color == "#FFD700"  # favorito gold border


def test_render_grid_empty():
    fig = render_grid({}, [], make_shelves())
    assert fig is not None
    assert len(fig.layout.shapes) == 4


def test_render_grid_multiple_shelves():
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=2),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2),
    ]
    assignment = {1: (1, 0, 0), 2: (2, 0, 1)}
    cars = [Car(id=1, modelo="A", cor_hex="#FF0000"), Car(id=2, modelo="B", cor_hex="#0000FF")]
    fig = render_grid(assignment, cars, shelves)
    assert len(fig.layout.shapes) == 4  # 1x2 + 1x2
