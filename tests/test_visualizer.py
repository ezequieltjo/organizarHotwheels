from models import Car, ShelfConfig, ParedeConfig
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
    # 1 shelf border + 4 cells
    assert len(fig.layout.shapes) == 5


def test_render_grid_shape_colors():
    fig = render_grid(make_assignment(), make_cars(), make_shelves())
    shapes = [s for s in fig.layout.shapes if s.fillcolor != "rgba(0,0,0,0)"]
    assert shapes[0].fillcolor == "#FF0000"  # car 1
    assert shapes[1].fillcolor == "#0000FF"  # car 2
    assert shapes[2].fillcolor == "#00FF00"  # car 3
    assert shapes[3].fillcolor == "#F0F0F0"  # empty


def test_render_grid_favorite_border():
    fig = render_grid(make_assignment(), make_cars(), make_shelves())
    shapes = [s for s in fig.layout.shapes if s.fillcolor != "rgba(0,0,0,0)"]
    assert shapes[0].line.color == "#FFD700"  # favorito gold border


def test_render_grid_empty():
    fig = render_grid({}, [], make_shelves())
    assert fig is not None
    assert len(fig.layout.shapes) == 5  # 1 border + 4 cells


def test_render_grid_multiple_shelves():
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=2),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2),
    ]
    assignment = {1: (1, 0, 0), 2: (2, 0, 1)}
    cars = [Car(id=1, modelo="A", cor_hex="#FF0000"), Car(id=2, modelo="B", cor_hex="#0000FF")]
    fig = render_grid(assignment, cars, shelves)
    # 2 shelf borders + 4 cells
    assert len(fig.layout.shapes) == 6


def test_render_grid_wall_layout():
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=2, parede_linha=0, parede_coluna=0),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2, parede_linha=0, parede_coluna=1),
    ]
    wall = ParedeConfig(linhas=1, colunas=2)
    assignment = {1: (1, 0, 0), 2: (1, 0, 1), 3: (2, 0, 0)}
    cars = [
        Car(id=1, modelo="A", cor_hex="#FF0000"),
        Car(id=2, modelo="B", cor_hex="#0000FF"),
        Car(id=3, modelo="C", cor_hex="#00FF00"),
    ]
    fig = render_grid(assignment, cars, shelves, wall)
    assert fig is not None
    shapes = fig.layout.shapes
    # 2 shelf borders + 4 cells
    assert len(shapes) == 6
    cell_shapes = [s for s in shapes if s.fillcolor != "rgba(0,0,0,0)"]
    assert len(cell_shapes) == 4
    # P1 offset=0, P2 offset=2 (no gap). P2 last cell: x1 = 2+1+0.5 = 3.5
    assert cell_shapes[-1].x1 == 3.5


def test_render_grid_wall_without_wall_fallback():
    shelves = make_shelves()
    fig = render_grid(make_assignment(), make_cars(), shelves, wall=None)
    assert fig is not None
    assert len(fig.layout.shapes) == 5  # 1 border + 4 cells
