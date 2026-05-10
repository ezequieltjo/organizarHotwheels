import random
from models import Car, ShelfConfig, ParedeConfig
from color_utils import hex_para_hue, distancia_rgb

# assignment = {car_id: (shelf_id, row, col)}


def organize_rainbow(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None) -> dict:
    sorted_cars = sorted(cars, key=lambda c: hex_para_hue(c.cor_hex))
    return _dispatch_fill(sorted_cars, shelves, wall)


def organize_gradient(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None) -> dict:
    if not cars:
        return {}
    ordered = _nearest_neighbor_sort(cars)
    return _dispatch_fill(ordered, shelves, wall)


def organize_by_brand(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None) -> dict:
    sorted_cars = sorted(cars, key=lambda c: (c.marca, c.cor))
    return _dispatch_fill(sorted_cars, shelves, wall)


def organize_by_fabricante(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None) -> dict:
    sorted_cars = sorted(cars, key=lambda c: (c.fabricante, c.cor))
    return _dispatch_fill(sorted_cars, shelves, wall)


def organize_by_year(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None) -> dict:
    sorted_cars = sorted(cars, key=lambda c: c.ano)
    return _dispatch_fill(sorted_cars, shelves, wall)


def organize_random(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None) -> dict:
    shuffled = list(cars)
    random.shuffle(shuffled)
    return _dispatch_fill(shuffled, shelves, wall)


def organize_favorites_first(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None) -> dict:
    favs = [c for c in cars if c.favorito]
    rest = [c for c in cars if not c.favorito]
    return _dispatch_fill(favs + rest, shelves, wall)


def total_slots(shelves: list[ShelfConfig]) -> int:
    return sum(s.linhas * s.colunas for s in shelves)


def _dispatch_fill(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None) -> dict:
    if wall and (wall.linhas > 1 or wall.colunas > 1):
        return _fill_wall_grid(cars, shelves, wall)
    return _fill_grid(cars, shelves)


def _fill_wall_grid(cars: list[Car], shelves: list[Car], wall: ParedeConfig) -> dict:
    # Build grid: wall_grid[r][c] = shelf or None
    wall_grid = [[None] * wall.colunas for _ in range(wall.linhas)]
    for shelf in shelves:
        r, c = shelf.parede_linha, shelf.parede_coluna
        if 0 <= r < wall.linhas and 0 <= c < wall.colunas:
            wall_grid[r][c] = shelf

    assignment = {}
    idx = 0
    for wall_row in range(wall.linhas):
        max_rows = max((s.linhas for s in wall_grid[wall_row] if s), default=0)
        for shelf_row in range(max_rows):
            for wall_col in range(wall.colunas):
                shelf = wall_grid[wall_row][wall_col]
                if not shelf or shelf_row >= shelf.linhas:
                    continue
                for col in range(shelf.colunas):
                    if idx >= len(cars):
                        return assignment
                    assignment[cars[idx].id] = (shelf.id, shelf_row, col)
                    idx += 1
    return assignment


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
