from models import Car, ShelfConfig, ParedeConfig
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        organize_favorites_first, total_slots, _fill_grid, _fill_wall_grid)


def make_cars():
    return [
        Car(id=1, modelo="A", cor_hex="#FF0000", cor="vermelho", marca="Chevrolet", fabricante="Hot Wheels", ano=2023, favorito=False),
        Car(id=2, modelo="B", cor_hex="#0000FF", cor="azul", marca="Ford", fabricante="Matchbox", ano=2022, favorito=True),
        Car(id=3, modelo="C", cor_hex="#00FF00", cor="verde", marca="Chevrolet", fabricante="Hot Wheels", ano=2024, favorito=False),
    ]


def make_shelves():
    return [ShelfConfig(id=1, nome="P1", linhas=2, colunas=2)]


def test_total_slots():
    shelves = make_shelves()
    assert total_slots(shelves) == 4


def test_fill_grid_basic():
    cars = make_cars()
    shelves = make_shelves()
    result = _fill_grid(cars, shelves)
    assert len(result) == 3
    assert result[1] == (1, 0, 0)
    assert result[2] == (1, 0, 1)
    assert result[3] == (1, 1, 0)


def test_fill_grid_overflow():
    cars = make_cars()
    shelves = [ShelfConfig(id=1, nome="P1", linhas=1, colunas=1)]
    result = _fill_grid(cars, shelves)
    assert len(result) == 1


def test_fill_grid_multiple_shelves():
    cars = make_cars()
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=1),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2),
    ]
    result = _fill_grid(cars, shelves)
    assert len(result) == 3
    assert result[1] == (1, 0, 0)
    assert result[2] == (2, 0, 0)
    assert result[3] == (2, 0, 1)


def test_organize_rainbow():
    cars = make_cars()
    result = organize_rainbow(cars, make_shelves())
    ids = list(result.keys())
    assert ids[0] == 1  # vermelho hue 0.0
    assert ids[1] == 3  # verde hue ~0.33
    assert ids[2] == 2  # azul hue ~0.66


def test_organize_by_brand():
    cars = make_cars()
    result = organize_by_brand(cars, make_shelves())
    ids = list(result.keys())
    assert ids[0] == 3  # Chevrolet, cor=verde
    assert ids[1] == 1  # Chevrolet, cor=vermelho
    assert ids[2] == 2  # Ford


def test_organize_by_fabricante():
    cars = make_cars()
    result = organize_by_fabricante(cars, make_shelves())
    ids = list(result.keys())
    assert ids[0] == 3  # Hot Wheels, cor=verde
    assert ids[1] == 1  # Hot Wheels, cor=vermelho
    assert ids[2] == 2  # Matchbox


def test_organize_by_year():
    cars = make_cars()
    result = organize_by_year(cars, make_shelves())
    ids = list(result.keys())
    assert ids[0] == 2  # 2022
    assert ids[1] == 1  # 2023
    assert ids[2] == 3  # 2024


def test_organize_random():
    cars = make_cars()
    result = organize_random(cars, make_shelves())
    assert len(result) == 3
    assert set(result.keys()) == {1, 2, 3}


def test_organize_favorites_first():
    cars = make_cars()
    result = organize_favorites_first(cars, make_shelves())
    ids = list(result.keys())
    assert ids[0] == 2  # favorito primeiro


def test_organize_gradient():
    cars = make_cars()
    result = organize_gradient(cars, make_shelves())
    assert len(result) == 3
    assert set(result.keys()) == {1, 2, 3}


def test_organize_empty():
    result = organize_rainbow([], make_shelves())
    assert result == {}


# --- Wall grid tests ---

def test_fill_wall_grid_2x1():
    """2 shelves side by side (1 wall row, 2 wall cols) — flows across shelves"""
    cars = make_cars()
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=2, colunas=2, parede_linha=0, parede_coluna=0),
        ShelfConfig(id=2, nome="P2", linhas=2, colunas=2, parede_linha=0, parede_coluna=1),
    ]
    wall = ParedeConfig(linhas=1, colunas=2)
    result = _fill_wall_grid(cars, shelves, wall)
    assert len(result) == 3
    # Row 0 fills P1 col0, P1 col1, then P2 col0, P2 col1
    assert result[1] == (1, 0, 0)  # P1 row0 col0
    assert result[2] == (1, 0, 1)  # P1 row0 col1
    assert result[3] == (2, 0, 0)  # P2 row0 col0 (flows across!)


def test_fill_wall_grid_1x2():
    """2 shelves stacked (2 wall rows, 1 wall col)"""
    cars = make_cars()
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=2, parede_linha=0, parede_coluna=0),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2, parede_linha=1, parede_coluna=0),
    ]
    wall = ParedeConfig(linhas=2, colunas=1)
    result = _fill_wall_grid(cars, shelves, wall)
    assert len(result) == 3
    assert result[1] == (1, 0, 0)
    assert result[2] == (1, 0, 1)
    assert result[3] == (2, 0, 0)


def test_fill_wall_grid_flows_across_wall_row():
    """Cars flow left→right across shelves in same wall row"""
    cars = make_cars()
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=1, parede_linha=0, parede_coluna=0),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2, parede_linha=0, parede_coluna=1),
    ]
    wall = ParedeConfig(linhas=1, colunas=2)
    result = _fill_wall_grid(cars, shelves, wall)
    assert len(result) == 3
    # First car fills P1 (only 1 slot)
    assert result[1] == (1, 0, 0)
    # Remaining cars flow to P2
    assert result[2] == (2, 0, 0)
    assert result[3] == (2, 0, 1)


def test_fill_wall_grid_empty_position():
    """Empty wall position is skipped"""
    cars = make_cars()
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=2, parede_linha=0, parede_coluna=0),
        # No shelf at (0, 1)
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2, parede_linha=1, parede_coluna=0),
    ]
    wall = ParedeConfig(linhas=2, colunas=2)
    result = _fill_wall_grid(cars, shelves, wall)
    assert len(result) == 3
    assert result[1] == (1, 0, 0)
    assert result[2] == (1, 0, 1)
    assert result[3] == (2, 0, 0)


def test_organize_rainbow_with_wall():
    cars = make_cars()
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=2, parede_linha=0, parede_coluna=0),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2, parede_linha=0, parede_coluna=1),
    ]
    wall = ParedeConfig(linhas=1, colunas=2)
    result = organize_rainbow(cars, shelves, wall)
    ids = list(result.keys())
    assert ids[0] == 1  # vermelho
    assert ids[1] == 3  # verde
    assert ids[2] == 2  # azul


def test_organize_without_wall_falls_back():
    """Without wall, uses sequential fill"""
    cars = make_cars()
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=1),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2),
    ]
    result = organize_rainbow(cars, shelves, wall=None)
    assert len(result) == 3
    # Same as _fill_grid sequential
    assert result[1] == (1, 0, 0)
