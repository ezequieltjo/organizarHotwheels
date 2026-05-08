import random
from models import Car, ShelfConfig
from color_utils import hex_para_hue, distancia_rgb

# assignment = {car_id: (shelf_id, row, col)}


def organize_rainbow(cars: list[Car], shelves: list[ShelfConfig]) -> dict:
    sorted_cars = sorted(cars, key=lambda c: hex_para_hue(c.cor_hex))
    return _fill_grid(sorted_cars, shelves)


def organize_gradient(cars: list[Car], shelves: list[ShelfConfig]) -> dict:
    if not cars:
        return {}
    ordered = _nearest_neighbor_sort(cars)
    return _fill_grid(ordered, shelves)


def organize_by_brand(cars: list[Car], shelves: list[ShelfConfig]) -> dict:
    sorted_cars = sorted(cars, key=lambda c: (c.marca, c.cor))
    return _fill_grid(sorted_cars, shelves)


def organize_by_fabricante(cars: list[Car], shelves: list[ShelfConfig]) -> dict:
    sorted_cars = sorted(cars, key=lambda c: (c.fabricante, c.cor))
    return _fill_grid(sorted_cars, shelves)


def organize_by_year(cars: list[Car], shelves: list[ShelfConfig]) -> dict:
    sorted_cars = sorted(cars, key=lambda c: c.ano)
    return _fill_grid(sorted_cars, shelves)


def organize_random(cars: list[Car], shelves: list[ShelfConfig]) -> dict:
    shuffled = list(cars)
    random.shuffle(shuffled)
    return _fill_grid(shuffled, shelves)


def organize_favorites_first(cars: list[Car], shelves: list[ShelfConfig]) -> dict:
    favs = [c for c in cars if c.favorito]
    rest = [c for c in cars if not c.favorito]
    return _fill_grid(favs + rest, shelves)


def total_slots(shelves: list[ShelfConfig]) -> int:
    return sum(s.linhas * s.colunas for s in shelves)


def _fill_grid(cars: list[Car], shelves: list[ShelfConfig]) -> dict:
    assignment = {}
    idx = 0
    for shelf in shelves:
        for row in range(shelf.linhas):
            for col in range(shelf.colunas):
                if idx >= len(cars):
                    return assignment
                assignment[cars[idx].id] = (shelf.id, row, col)
                idx += 1
    return assignment


def _nearest_neighbor_sort(cars: list[Car]) -> list[Car]:
    remaining = list(cars)
    ordered = [remaining.pop(0)]
    while remaining:
        last = ordered[-1]
        nearest = min(remaining, key=lambda c: distancia_rgb(last.cor_hex, c.cor_hex))
        remaining.remove(nearest)
        ordered.append(nearest)
    return ordered
