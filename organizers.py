import random
import colorsys
from models import Car, ShelfConfig, ParedeConfig, GradientConfig
from color_utils import hex_para_rgb, distancia_rgb

# assignment = {car_id: (shelf_id, row, col)}


def _is_blocked(shelf_id: int, row: int, col: int, disabled: dict | None) -> bool:
    if not disabled:
        return False
    d = disabled.get(shelf_id)
    if not d:
        return False
    return row in d["rows"] or (row, col) in d["cells"]


def _filter_reserva(cars: list[Car]) -> list[Car]:
    """Exclui carros marcados como reserva da organizacao."""
    return [c for c in cars if not c.reserva]


def organize_rainbow(cars: list[Car], shelves: list[ShelfConfig],
                     wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    """Arco-íris com moldura cinza: coloridos por hue no miolo, cinzas no anel."""
    cars = _filter_reserva(cars)
    if not cars:
        return {}
    return _ring_fill(cars, shelves, wall, disabled,
                      GradientConfig(interior_strategy="arcoiris"))


def organize_gradient(cars: list[Car], shelves: list[ShelfConfig],
                      wall: ParedeConfig = None, disabled: dict | None = None,
                      config: GradientConfig | None = None) -> dict:
    cars = _filter_reserva(cars)
    if not cars:
        return {}
    cfg = config or GradientConfig()
    return _ring_fill(cars, shelves, wall, disabled, cfg)


def organize_by_brand(cars: list[Car], shelves: list[ShelfConfig],
                     wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    sorted_cars = sorted(cars, key=lambda c: (c.marca, c.cor))
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)


def organize_by_fabricante(cars: list[Car], shelves: list[ShelfConfig],
                           wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    sorted_cars = sorted(cars, key=lambda c: (c.fabricante, c.cor))
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)


def organize_by_year(cars: list[Car], shelves: list[ShelfConfig],
                    wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    sorted_cars = sorted(cars, key=lambda c: c.ano)
    return _dispatch_fill(sorted_cars, shelves, wall, disabled)


def organize_random(cars: list[Car], shelves: list[ShelfConfig],
                    wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
    shuffled = list(cars)
    random.shuffle(shuffled)
    return _dispatch_fill(shuffled, shelves, wall, disabled)


def organize_favorites_first(cars: list[Car], shelves: list[ShelfConfig],
                             wall: ParedeConfig = None, disabled: dict | None = None) -> dict:
    cars = _filter_reserva(cars)
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


def _is_gray(hex_color: str, sat_threshold: float) -> bool:
    """True se saturação HSV <= sat_threshold (escala 0-1).

    Preto, branco e cinzas neutros (sat ~ 0) sempre contam como cinza.
    """
    _, s, _ = _hex_to_hsv(hex_color)
    return s <= sat_threshold


def _ring_cells(rows: int, cols: int, offset: int = 0) -> list[tuple[int, int]]:
    """Células do perímetro da sub-grade com offset, em sentido horário.

    Começa em (offset, offset + cols//2) [preto] e termina em
    (offset, offset + cols//2 - 1) [branco]. Requer rows >= 2 e cols >= 2.
    """
    r0, c0 = offset, offset
    r1, c1 = offset + rows - 1, offset + cols - 1
    seam_right = offset + cols // 2      # preto
    seam_left = offset + cols // 2 - 1   # branco (adjacente ao preto)
    cells: list[tuple[int, int]] = []
    for c in range(seam_right, c1 + 1):          # topo direita -> canto sup-direito
        cells.append((r0, c))
    for r in range(r0 + 1, r1 + 1):              # borda direita (descendo)
        cells.append((r, c1))
    for c in range(c1 - 1, c0 - 1, -1):          # fundo (direita -> esquerda)
        cells.append((r1, c))
    for r in range(r1 - 1, r0, -1):              # borda esquerda (subindo)
        cells.append((r, c0))
    for c in range(c0, seam_left + 1):           # topo esquerda -> branco
        cells.append((r0, c))
    return cells


def _ordered_cells(rows: int, cols: int) -> list[tuple[int, int]]:
    """Todas as células: anel externo -> internos -> miolo, em ordem.

    Cada anel é percorrido em sentido horário. O miolo final degenerado
    (1 linha/coluna) é preenchido em row-major. Segura para rows, cols >= 1.
    """
    cells: list[tuple[int, int]] = []
    offset = 0
    while True:
        h = rows - 2 * offset
        w = cols - 2 * offset
        if h <= 0 or w <= 0:
            break
        if h < 2 or w < 2:
            for r in range(offset, offset + h):
                for c in range(offset, offset + w):
                    cells.append((r, c))
            break
        cells.extend(_ring_cells(h, w, offset))
        offset += 1
    return list(dict.fromkeys(cells))


def _find_nearest_allowed(grid, row: int, col: int, allowed: set[tuple[int, int]], total_rows: int, total_cols: int) -> tuple[int, int] | None:
    """Célula vazia mais próxima de (row, col) dentro do conjunto permitido.

    Raio cobre a distância de Manhattan máxima possível, (R-1)+(C-1),
    alcançando qualquer célula do grid retangular.
    """
    if (row, col) in allowed:
        return (row, col)
    for dist in range(1, total_rows + total_cols):
        for dr in range(-dist, dist + 1):
            for dc in range(-dist, dist + 1):
                if abs(dr) + abs(dc) != dist:
                    continue
                cell = (row + dr, col + dc)
                if cell in allowed:
                    return cell
    return None


def _place_grays(grid: list, grays: list, outer_ring: list[tuple[int, int]], strategy: str) -> None:
    """Posiciona cinzas (já ordenados preto->branco) no anel externo.

    estica (e poucos cinzas): distribui uniformemente pelo anel externo.
    caso geral: preenche o anel externo; excedentes ficam a cargo de
    _place_overflow_grays.
    """
    if not grays:
        return
    rows, cols = len(grid), len(grid[0])
    n = len(grays)
    if strategy == "estica" and n < len(outer_ring):
        ring_len = len(outer_ring)
        for i, (car, _h, _s, _v) in enumerate(grays):
            if n > 1:
                idx = round(i * (ring_len - 1) / (n - 1))
            else:
                idx = 0
            r, c = outer_ring[idx]
            if grid[r][c] is None:
                grid[r][c] = car
            else:
                er, ec = _find_nearest_empty(grid, r, c, rows, cols)
                if er is not None:
                    grid[er][ec] = car
        return
    for (car, _h, _s, _v), (r, c) in zip(grays, outer_ring):
        if grid[r][c] is None:
            grid[r][c] = car
        else:
            er, ec = _find_nearest_empty(grid, r, c, rows, cols)
            if er is not None:
                grid[er][ec] = car


# Limiares de value (HSV) para classificar cinzas excedentes.
BLACK_V = 0.15
WHITE_V = 0.85


def _corner_cells(rows: int, cols: int, anchor: tuple[int, int]) -> list[tuple[int, int]]:
    """Células em cascas concêntricas (distância Chebyshev) a partir da quina."""
    ar, ac = anchor
    return sorted(((r, c) for r in range(rows) for c in range(cols)),
                  key=lambda rc: (max(abs(rc[0] - ar), abs(rc[1] - ac)), rc))


def _split_overflow(grays: list, ring_cap: int) -> tuple[list, list]:
    """Separa cinzas entre anel e quinas quando excedem a capacidade do anel.

    Quota proporcional ao tamanho de cada grupo de tom (preto/cinza/branco),
    para que todas as pontas recebam carros (balanço simétrico) em vez de
    transbordar só o extremo claro. Pretos e brancos saem pelos extremos
    (mais escuros / mais claros); cinzas médios saem pela janela central da
    faixa — os cantos inferiores do anel têm tons medianos, então os cinzas
    mais medianos é que fazem match. O anel mantém o gradiente com o resto.
    """
    excess = len(grays) - ring_cap
    if excess <= 0:
        return grays, []
    total = len(grays)
    idx_black = [i for i, g in enumerate(grays) if g[3] <= BLACK_V]
    idx_mid = [i for i, g in enumerate(grays) if BLACK_V < g[3] < WHITE_V]
    idx_white = [i for i, g in enumerate(grays) if g[3] >= WHITE_V]

    corner: set[int] = set()
    cum = 0
    for grp, mode in ((idx_black, "dark"), (idx_mid, "mid"), (idx_white, "light")):
        prev = round(excess * cum / total)
        cum += len(grp)
        q = min(len(grp), round(excess * cum / total) - prev)
        if q <= 0:
            continue
        if mode == "dark":
            corner.update(grp[:q])
        elif mode == "light":
            corner.update(grp[-q:])
        else:  # cinzas: janela central (tons próximos dos cantos inferiores)
            start = (len(grp) - q) // 2
            corner.update(grp[start:start + q])
    ring = [g for i, g in enumerate(grays) if i not in corner]
    corners = [g for i, g in enumerate(grays) if i in corner]
    return ring, corners


def _corner_tone(grid: list, cell: tuple[int, int]) -> float | None:
    """Value (HSV) do carro na célula, ou None se vazia."""
    car = grid[cell[0]][cell[1]]
    if car is None:
        return None
    return _hex_to_hsv(car.cor_hex)[2]


def _corner_segments(grid: list, grays: list) -> list:
    """Agrupa cinzas excedentes por quina, ordenados pela proximidade ao
    tom do canto (mais parecido primeiro): brancos no canto sup-esquerdo,
    pretos no sup-direito, cinzas médios nos inferiores — cada um no canto
    cujo tom do anel é o mais próximo do seu."""
    if not grays:
        return []
    rows, cols = len(grid), len(grid[0])
    blacks = [g for g in grays if g[3] <= BLACK_V]
    whites = [g for g in grays if g[3] >= WHITE_V]
    mids = [g for g in grays if BLACK_V < g[3] < WHITE_V]

    right_tone = _corner_tone(grid, (rows - 1, cols - 1))
    left_tone = _corner_tone(grid, (rows - 1, 0))
    mids_right, mids_left = [], []
    if right_tone is None and left_tone is None:
        half = (len(mids) + 1) // 2
        mids_right, mids_left = mids[:half], mids[half:]
    else:
        rt = right_tone if right_tone is not None else left_tone
        lt = left_tone if left_tone is not None else right_tone
        for g in mids:
            dr, dl = abs(g[3] - rt), abs(g[3] - lt)
            # tolerância p/ empate exato que o float quebraria por ruído
            if dr < dl - 1e-9 or (abs(dr - dl) <= 1e-9 and rt <= lt):
                mids_right.append(g)
            else:
                mids_left.append(g)

    segs = [
        (whites, (0, 0)),                       # canto sup-esquerdo
        (blacks, (0, cols - 1)),                # canto sup-direito
        (mids_right, (rows - 1, cols - 1)),     # inf-direito
        (mids_left, (rows - 1, 0)),             # inf-esquerdo
    ]
    ordered = []
    for cars, anchor in segs:
        # tom mais parecido com o canto fica na célula mais perto da
        # quina; diverge gradualmente crescendo na diagonal
        tone = _corner_tone(grid, anchor)
        if tone is not None:
            cars = sorted(cars, key=lambda g: abs(g[3] - tone))
        ordered.append((cars, anchor))
    return ordered


def _reserved_corner_cells(grid: list, segs: list, slot_cells: set) -> set:
    """Células livres mais próximas de cada quina, reservadas aos seus cinzas.

    Coloridos não podem ocupá-las — garante que nas quinas nenhum colorido
    fique mais perto da ponta que um cinza daquele grupo."""
    reserved = set()
    if not segs:
        return reserved
    rows, cols = len(grid), len(grid[0])
    for cars, anchor in segs:
        need = len(cars)
        for r, c in _corner_cells(rows, cols, anchor):
            if need == 0:
                break
            if (r, c) in slot_cells and grid[r][c] is None:
                reserved.add((r, c))
                need -= 1
    return reserved


def _place_overflow_grays(grid: list, segs: list) -> None:
    """Posiciona os grupos de cinzas nas suas quinas, célula mais próxima
    da ponta primeiro (cresce na diagonal para o centro)."""
    rows, cols = len(grid), len(grid[0])
    for cars, anchor in segs:
        i = 0
        for r, c in _corner_cells(rows, cols, anchor):
            if i >= len(cars):
                break
            if grid[r][c] is None:
                grid[r][c] = cars[i][0]
                i += 1


def _place_chroma(grid: list, chroma: list, total_rows: int, total_cols: int,
                  outer_set: set[tuple[int, int]], cfg: GradientConfig,
                  reserved: set | None = None, slot_cells: set | None = None) -> None:
    """Posiciona coloridos no miolo (e perímetro, conforme estratégia).

    Evita células reservadas às quinas (reserved) e, quando slot_cells é
    informado, células sem slot real (evita remapeamento na conversão)."""
    if not chroma:
        return
    allowed = {(r, c) for r in range(total_rows) for c in range(total_cols)
               if grid[r][c] is None}
    if slot_cells is not None:
        allowed &= slot_cells
    if reserved:
        allowed -= reserved
    if cfg.partial_strategy == "vazio":
        allowed = {cell for cell in allowed if cell not in outer_set}

    if cfg.interior_strategy in ("similaridade", "arcoiris"):
        if cfg.interior_strategy == "similaridade":
            ordered = _nearest_neighbor_sort([c[0] for c in chroma])
        else:  # arcoiris: sequência por matiz (hue)
            ordered = [c[0] for c in sorted(chroma, key=lambda x: x[1])]
        interior = sorted(cell for cell in allowed if cell not in outer_set)
        perimeter = sorted(cell for cell in allowed if cell in outer_set)
        seq = interior + perimeter
        for car, cell in zip(ordered, seq):
            grid[cell[0]][cell[1]] = car
        return

    # hue_value: miolo-first quando colorido; vazio já excluiu o perímetro.
    interior_allowed = {cell for cell in allowed if cell not in outer_set}
    perimeter_allowed = {cell for cell in allowed if cell in outer_set}
    for car, h, _s, v in chroma:
        target_col = int(h * total_cols) % total_cols
        target_row = int((1.0 - v) * total_rows) if total_rows > 1 else 0
        target_row = min(max(target_row, 0), total_rows - 1)
        cell = _find_nearest_allowed(grid, target_row, target_col,
                                     interior_allowed, total_rows, total_cols)
        if cell is None:
            cell = _find_nearest_allowed(grid, target_row, target_col,
                                         perimeter_allowed, total_rows, total_cols)
        if cell is None:
            continue
        grid[cell[0]][cell[1]] = car
        interior_allowed.discard(cell)
        perimeter_allowed.discard(cell)


def _grid_to_assignment(grid: list, cars: list, slot_map: dict, total_rows: int, total_cols: int) -> dict:
    """Converte a grade virtual em assignment {car_id: (shelf_id, row, col)}."""
    assignment = {}
    used = set()
    for r in range(total_rows):
        for c in range(total_cols):
            car = grid[r][c]
            if car is None or car.id in assignment:
                continue
            if (r, c) in slot_map and (r, c) not in used:
                assignment[car.id] = slot_map[(r, c)]
                used.add((r, c))
            else:
                found = _find_nearest_real_slot(slot_map, used, r, c, total_rows, total_cols)
                if found:
                    assignment[car.id] = slot_map[found]
                    used.add(found)
    remaining_cars = [car for car in cars if car.id not in assignment]
    remaining_slots = [pos for pos in slot_map if pos not in used]
    for car, pos in zip(remaining_cars, remaining_slots):
        assignment[car.id] = slot_map[pos]
        used.add(pos)
    return assignment


def _ring_fill(cars: list[Car], shelves: list[ShelfConfig],
               wall: ParedeConfig | None, disabled: dict | None,
               cfg: GradientConfig) -> dict:
    """Posiciona cinzas como moldura (anel horário) ao redor dos coloridos."""
    slots = _build_slot_list(shelves, wall, disabled)
    if not slots:
        return {}
    total_rows = max(s[3] for s in slots) + 1
    total_cols = max(s[4] for s in slots) + 1
    slot_map = {(gr, gc): (sid, sr, sc) for sid, sr, sc, gr, gc in slots}

    sat = cfg.sat_threshold_pct / 100.0
    grays, chroma = [], []
    for car in cars:
        h, s, v = _hex_to_hsv(car.cor_hex)
        (grays if _is_gray(car.cor_hex, sat) else chroma).append((car, h, s, v))
    grays.sort(key=lambda x: x[3])  # preto (value baixo) primeiro

    grid = [[None] * total_cols for _ in range(total_rows)]
    if total_rows >= 2 and total_cols >= 2:
        outer_ring = [c for c in _ring_cells(total_rows, total_cols, 0) if c in slot_map]
    else:
        outer_ring = [c for c in _ordered_cells(total_rows, total_cols) if c in slot_map]
    outer_set = set(outer_ring)

    ring_grays, corner_grays = _split_overflow(grays, len(outer_ring))
    _place_grays(grid, ring_grays, outer_ring, cfg.partial_strategy)
    slot_cells = set(slot_map)
    segs = _corner_segments(grid, corner_grays)
    reserved = _reserved_corner_cells(grid, segs, slot_cells)
    _place_chroma(grid, chroma, total_rows, total_cols, outer_set, cfg,
                  reserved=reserved, slot_cells=slot_cells)
    _place_overflow_grays(grid, segs)

    return _grid_to_assignment(grid, cars, slot_map, total_rows, total_cols)


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
