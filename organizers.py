import random
import colorsys
from models import Car, ShelfConfig, ParedeConfig
from color_utils import hex_para_hue, hex_para_rgb, distancia_rgb

# assignment = {car_id: (shelf_id, row, col)}


def _is_blocked(shelf_id: int, row: int, col: int, disabled: dict | None) -> bool:
    if not disabled:
        return False
    d = disabled.get(shelf_id)
    if not d:
        return False
    return row in d["rows"] or (row, col) in d["cells"]


def organize_rainbow(cars: list[Car], shelves: list[ShelfConfig],
                     wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    sorted_cars = sorted(cars, key=lambda c: hex_para_hue(c.cor_hex))
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)


def organize_gradient(cars: list[Car], shelves: list[ShelfConfig],
                      wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    if not cars:
        return {}
    return _gradient_2d_fill(cars, shelves, wall, disabled)


def organize_by_brand(cars: list[Car], shelves: list[ShelfConfig],
                     wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    sorted_cars = sorted(cars, key=lambda c: (c.marca, c.cor))
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)


def organize_by_fabricante(cars: list[Car], shelves: list[ShelfConfig],
                           wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    sorted_cars = sorted(cars, key=lambda c: (c.fabricante, c.cor))
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)


def organize_by_year(cars: list[Car], shelves: list[ShelfConfig],
                    wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    sorted_cars = sorted(cars, key=lambda c: c.ano)
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)


def organize_random(cars: list[Car], shelves: list[ShelfConfig],
                    wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    shuffled = list(cars)
    random.shuffle(shuffled)
    return _dispatch_fill(shuffled, shelves, wall, disabled)


def organize_favorites_first(cars: list[Car], shelves: list[ShelfConfig],
                             wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    favs = [c for c in cars if c.favorito]
    rest = [c for c in cars if not c.favorito]
    return _dispatch_fill(favs + rest, shelves, wall, disabled)


def total_slots(shelves: list[ShelfConfig], disabled: dict | None = None) -> int:
    total = sum(s.linhas * s.colunas for s in shelves)
    if not disabled:
        return total
    blocked = 0
    for s in shelves:
        d = disabled.get(s.id)
        if not d:
            continue
        for row in range(s.linhas):
            if row in d["rows"]:
                blocked += s.colunas
                continue
            blocked += sum(1 for col in range(s.colunas) if (row, col) in d["cells"])
    return total - blocked


def _dispatch_fill(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None,
                   disabled: dict | None = None) -> dict:
    if wall and (wall.linhas > 1 or wall.colunas > 1):
        return _fill_wall_grid(cars, shelves, wall, disabled)
    return _fill_grid(cars, shelves, disabled)


def _fill_wall_grid(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig,
                    disabled: dict | None = None) -> dict:
    # Build grid: wall_grid[r][c] = shelf or None
    wall_grid = [[None] * wall.colunas for _ in range(wall.linhas)]
    for shelf in shelves:
        r, c = shelf.parede_linha, shelf.parede_coluna
        if 0 <= r < wall.linhas and 0 <= c < wall.colunas:
            wall_grid[r][c] = shelf

    assignment = {}
    idx = 0
    global_row = 0
    for wall_row in range(wall.linhas):
        max_rows = max((s.linhas for s in wall_grid[wall_row] if s), default=0)
        for shelf_row in range(max_rows):
            # snake: even rows L→R, odd rows R→L
            wall_cols = range(wall.colunas) if global_row % 2 == 0 else range(wall.colunas - 1, -1, -1)
            for wall_col in wall_cols:
                shelf = wall_grid[wall_row][wall_col]
                if not shelf or shelf_row >= shelf.linhas:
                    continue
                n = shelf.colunas
                cols = range(n) if global_row % 2 == 0 else range(n - 1, -1, -1)
                for col in cols:
                    if _is_blocked(shelf.id, shelf_row, col, disabled):
                        continue
                    if idx >= len(cars):
                        return assignment
                    assignment[cars[idx].id] = (shelf.id, shelf_row, col)
                    idx += 1
            global_row += 1
    return assignment


def _fill_grid(cars: list[Car], shelves: list[ShelfConfig], disabled: dict | None = None) -> dict:
    assignment = {}
    idx = 0
    for shelf in shelves:
        for row in range(shelf.linhas):
            cols = range(shelf.colunas) if row % 2 == 0 else range(shelf.colunas - 1, -1, -1)
            for col in cols:
                if _is_blocked(shelf.id, row, col, disabled):
                    continue
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


def _hex_to_hsv(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)


def _gradient_2d_fill(cars: list[Car], shelves: list[ShelfConfig], wall: ParedeConfig = None,
                      disabled: dict | None = None) -> dict:
    # Build slot list: (shelf_id, shelf_row, shelf_col, global_row, global_col)
    slots = _build_slot_list(shelves, wall, disabled)
    if not slots:
        return {}

    total_rows = max(s[3] for s in slots) + 1
    total_cols = max(s[4] for s in slots) + 1

    # Classify colors
    gray_cars = []
    chroma_cars = []
    for car in cars:
        h, s, v = _hex_to_hsv(car.cor_hex)
        if s < 0.12:
            gray_cars.append((car, h, s, v))
        else:
            chroma_cars.append((car, h, s, v))

    chroma_cars.sort(key=lambda x: x[1])
    gray_cars.sort(key=lambda x: x[3], reverse=True)

    # Build target grid indexed by (global_row, global_col) → car or None
    grid = [[None] * total_cols for _ in range(total_rows)]
    # Map (global_row, global_col) → real slot (shelf_id, shelf_row, shelf_col)
    slot_map = {}
    for shelf_id, sr, sc, gr, gc in slots:
        slot_map[(gr, gc)] = (shelf_id, sr, sc)

    n_gray = len(gray_cars)
    n_chroma = len(chroma_cars)
    n_rows_chroma = max(1, round(total_rows * n_chroma / max(1, n_chroma + n_gray))) if n_gray > 0 else total_rows
    n_rows_gray_top = (total_rows - n_rows_chroma) // 2
    n_rows_gray_bot = total_rows - n_rows_chroma - n_rows_gray_top

    # Place chromatic cars in middle band
    for i, (car, h, s, v) in enumerate(chroma_cars):
        col = int(h * total_cols) % total_cols
        row_in_band = int((1.0 - v) * n_rows_chroma) if n_rows_chroma > 1 else 0
        row_in_band = min(row_in_band, n_rows_chroma - 1)
        row = n_rows_gray_top + row_in_band
        row, col = _find_nearest_empty(grid, row, col, total_rows, total_cols)
        if row is not None:
            grid[row][col] = car

    # Place gray cars
    top_grays = gray_cars[:n_gray // 2]
    bot_grays = gray_cars[n_gray // 2:]
    for band_start, band_size, gray_list in [
        (0, n_rows_gray_top, top_grays),
        (total_rows - n_rows_gray_bot, n_rows_gray_bot, bot_grays),
    ]:
        if band_size == 0:
            continue
        for i, (car, h, s, v) in enumerate(gray_list):
            col = i % total_cols
            row_in_band = min(i // total_cols, band_size - 1)
            row = band_start + row_in_band
            row, col = _find_nearest_empty(grid, row, col, total_rows, total_cols)
            if row is not None:
                grid[row][col] = car

    # Build assignment from grid → real slot coordinates
    assignment = {}
    used = set()
    for r in range(total_rows):
        for c in range(total_cols):
            car = grid[r][c]
            if car is None or car.id in assignment:
                continue
            if (r, c) in slot_map and (r, c) not in used:
                real = slot_map[(r, c)]
                assignment[car.id] = real
                used.add((r, c))
            else:
                # Find nearest real slot
                found = _find_nearest_real_slot(slot_map, used, r, c, total_rows, total_cols)
                if found:
                    assignment[car.id] = slot_map[found]
                    used.add(found)

    # Remaining cars → remaining slots
    remaining_cars = [c for c in cars if c.id not in assignment]
    all_slots = [(gr, gc) for gr, gc in slot_map if (gr, gc) not in used]
    for car, pos in zip(remaining_cars, all_slots):
        assignment[car.id] = slot_map[pos]
        used.add(pos)

    return assignment


def _build_slot_list(shelves: list[ShelfConfig], wall: ParedeConfig = None,
                     disabled: dict | None = None) -> list[tuple]:
    """Returns [(shelf_id, shelf_row, shelf_col, global_row, global_col), ...]"""
    if wall and (wall.linhas > 1 or wall.colunas > 1):
        wall_grid = [[None] * wall.colunas for _ in range(wall.linhas)]
        for shelf in shelves:
            r, c = shelf.parede_linha, shelf.parede_coluna
            if 0 <= r < wall.linhas and 0 <= c < wall.colunas:
                wall_grid[r][c] = shelf

        col_offsets = []
        offset = 0
        for wall_col in range(wall.colunas):
            col_offsets.append(offset)
            max_w = max((wall_grid[wr][wall_col].colunas for wr in range(wall.linhas)
                        if wall_grid[wr][wall_col]), default=0)
            offset += max_w

        slots = []
        global_row = 0
        for wall_row in range(wall.linhas):
            max_rows = max((s.linhas for s in wall_grid[wall_row] if s), default=0)
            for shelf_row in range(max_rows):
                for wall_col in range(wall.colunas):
                    shelf = wall_grid[wall_row][wall_col]
                    if not shelf or shelf_row >= shelf.linhas:
                        continue
                    gc = col_offsets[wall_col]
                    for col in range(shelf.colunas):
                        slots.append((shelf.id, shelf_row, col, global_row, gc + col))
                global_row += 1
    else:
        slots = []
        global_row = 0
        for shelf in shelves:
            for row in range(shelf.linhas):
                for col in range(shelf.colunas):
                    slots.append((shelf.id, row, col, global_row, col))
                global_row += 1
    if disabled:
        slots = [s for s in slots if not _is_blocked(s[0], s[1], s[2], disabled)]
    return slots


def _find_nearest_real_slot(slot_map, used, row, col, total_rows, total_cols):
    best = None
    best_dist = float('inf')
    for (r, c) in slot_map:
        if (r, c) in used:
            continue
        d = abs(r - row) + abs(c - col)
        if d < best_dist:
            best_dist = d
            best = (r, c)
    return best


def _find_nearest_empty(grid, row, col, total_rows, total_cols):
    if grid[row][col] is None:
        return row, col
    for dist in range(1, max(total_rows, total_cols)):
        for dr in range(-dist, dist + 1):
            for dc in range(-dist, dist + 1):
                if abs(dr) + abs(dc) != dist:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < total_rows and 0 <= nc < total_cols and grid[nr][nc] is None:
                    return nr, nc
    return None, None
