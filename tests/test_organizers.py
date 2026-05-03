from models import Car, ShelfConfig
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_year, organize_random, organize_favorites_first,
                        total_slots, _fill_grid)


def make_cars():
    return [
        Car(id=1, modelo="A", cor_hex="#FF0000", cor="vermelho", marca="Mattel", ano=2023, favorito=False),
        Car(id=2, modelo="B", cor_hex="#0000FF", cor="azul", marca="Hot Wheels", ano=2022, favorito=True),
        Car(id=3, modelo="C", cor_hex="#00FF00", cor="verde", marca="Mattel", ano=2024, favorito=False),
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
    assert ids[0] == 2  # Hot Wheels
    assert ids[1] == 3  # Mattel cor=verde (sorted by cor string)
    assert ids[2] == 1  # Mattel cor=vermelho


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
