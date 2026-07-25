from models import Car, ShelfConfig, ParedeConfig, GradientConfig
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        organize_favorites_first, total_slots, _fill_grid, _fill_wall_grid,
                        _is_gray, _ring_cells, _ordered_cells,
                        _place_grays, _place_chroma, _grid_to_assignment)


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


# --- gray classification (critério: saturação HSV <= limiar) ---

def test_is_gray_neutral():
    assert _is_gray("#808080", 0.12)   # cinza puro, s=0
    assert _is_gray("#8A8A8A", 0.12)   # cinza sujo, saturação baixa


def test_is_gray_pure_black_white():
    assert _is_gray("#000000", 0.12)
    assert _is_gray("#FFFFFF", 0.12)


def test_is_gray_saturated_is_chromatic():
    assert not _is_gray("#FF0000", 0.12)  # vermelho puro
    assert not _is_gray("#00FF00", 0.12)  # verde puro
    assert not _is_gray("#0000FF", 0.12)  # azul puro


def test_is_gray_dark_saturated_stays_chromatic():
    # vermelho quase-preto e navy: sat alta -> colorido (diferença vs regra antiga)
    assert not _is_gray("#0A0000", 0.12)
    assert not _is_gray("#000080", 0.12)


def test_is_gray_threshold_sensitivity():
    # #9090B0 sat ~0.18: abaixo do limiar=colorido, acima=cinza
    assert not _is_gray("#9090B0", 0.12)
    assert _is_gray("#9090B0", 0.25)


# --- ring perimeter order ---

def test_ring_cells_clockwise_from_seam():
    cells = _ring_cells(3, 3, 0)
    assert cells[0] == (0, 1)    # preto: centro-direita do topo (cols//2 = 1)
    assert cells[-1] == (0, 0)   # branco: centro-esquerda do topo (adjacente)
    assert cells[1] == (0, 2)    # topo direita
    assert cells[2] == (1, 2)    # borda direita descendo
    assert (1, 1) not in cells   # centro é miolo, não perímetro


def test_ring_cells_no_duplicates_and_full_perimeter():
    cells = _ring_cells(4, 5, 0)
    assert len(cells) == len(set(cells))           # sem duplicatas
    assert len(cells) == 2 * (4 + 5) - 4           # perímetro = 14


def test_ring_cells_offset_for_inner_ring():
    outer = _ring_cells(5, 5, 0)
    inner = _ring_cells(3, 3, 1)   # anel interno 3x3 com offset 1
    assert (1, 1) in inner
    assert set(outer).isdisjoint(set(inner))


# --- concentric ordered cells (outer ring -> inner rings -> center) ---

def test_ordered_cells_covers_all():
    cells = _ordered_cells(3, 6)
    assert len(cells) == len(set(cells)) == 3 * 6


def test_ordered_cells_outer_ring_first():
    cells = _ordered_cells(5, 5)
    outer = _ring_cells(5, 5, 0)
    assert cells[: len(outer)] == outer


def test_ordered_cells_single_row_safe():
    # degradado: 1 linha -> row-major, não quebra
    cells = _ordered_cells(1, 4)
    assert cells == [(0, 0), (0, 1), (0, 2), (0, 3)]


# --- gradient layout: cinzas nas bordas laterais, cromático no miolo ---

def _gray_cars():
    return [
        Car(id=10, modelo="g_claro", cor_hex="#FFFFFF", cor="", marca="",
            fabricante="", ano=2020, favorito=False),
        Car(id=11, modelo="g_medio", cor_hex="#808080", cor="", marca="",
            fabricante="", ano=2020, favorito=False),
        Car(id=12, modelo="g_escuro", cor_hex="#000000", cor="", marca="",
            fabricante="", ano=2020, favorito=False),
    ]


def test_gradient_gray_on_lateral_columns():
    cars = _gray_cars() + make_cars()  # 3 cinzas + 3 cromáticos
    shelves = [ShelfConfig(id=1, nome="P1", linhas=1, colunas=6)]
    result = organize_gradient(cars, shelves)
    gray_cols = {result[i][2] for i in (10, 11, 12)}
    chroma_cols = {result[i][2] for i in (1, 2, 3)}
    # cinzas nas bordas laterais, cromáticos no miolo (conjuntos disjuntos)
    assert gray_cols & chroma_cols == set()
    assert all(c in {0, 4, 5} for c in gray_cols)
    assert all(c in {1, 2, 3} for c in chroma_cols)


def test_gradient_gray_light_left_dark_right():
    """Metade clara dos cinzas à esquerda, metade escura à direita."""
    cars = [
        Car(id=20, modelo="branco", cor_hex="#FFFFFF", cor="", marca="",
            fabricante="", ano=2020, favorito=False),
        Car(id=21, modelo="prata", cor_hex="#C0C0C0", cor="", marca="",
            fabricante="", ano=2020, favorito=False),
        Car(id=22, modelo="grafite", cor_hex="#404040", cor="", marca="",
            fabricante="", ano=2020, favorito=False),
        Car(id=23, modelo="preto", cor_hex="#000000", cor="", marca="",
            fabricante="", ano=2020, favorito=False),
    ]
    shelves = [ShelfConfig(id=1, nome="P1", linhas=1, colunas=6)]
    result = organize_gradient(cars, shelves)
    light_cols = {result[20][2], result[21][2]}  # branco + prata
    dark_cols = {result[22][2], result[23][2]}   # grafite + preto
    mid = 3  # coluna central do expositor de 6 colunas
    # claros à esquerda do meio, escuros à direita, lados disjuntos
    assert all(c < mid for c in light_cols)
    assert all(c >= mid for c in dark_cols)
    assert light_cols & dark_cols == set()


def test_gradient_gray_vertical_light_to_dark():
    cars = _gray_cars()
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=1)]
    result = organize_gradient(cars, shelves)
    # claro no topo (row 0), escuro embaixo (row 2)
    assert result[10][1] == 0  # branco
    assert result[11][1] == 1  # cinza médio
    assert result[12][1] == 2  # preto


def test_gradient_no_gray_all_chromatic():
    # sem cinzas: não quebra, todos no miolo
    cars = make_cars()
    shelves = [ShelfConfig(id=1, nome="P1", linhas=1, colunas=6)]
    result = organize_gradient(cars, shelves)
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


# --- ring placement helpers (Task 5) ---

def _make_grid(rows, cols):
    return [[None] * cols for _ in range(rows)]


def _gray_car(cid, value01):
    v = int(value01 * 255)
    return Car(id=cid, modelo=f"g{cid}", cor_hex=f"#{v:02X}{v:02X}{v:02X}")


def test_place_grays_fill_outer_then_inner():
    grid = _make_grid(3, 6)
    all_cells = _ordered_cells(3, 6)
    outer = _ring_cells(3, 6, 0)
    grays = [(_gray_car(10, 0.0), 0, 0, 0.0), (_gray_car(11, 1.0), 0, 0, 1.0)]
    _place_grays(grid, grays, all_cells, outer, "colorido")
    assert grid[0][3].id == 10  # preto no seam_right (cols//2 = 3)
    assert grid[0][4].id == 11  # branco na próxima posição do anel


def test_place_grays_estica_spreads():
    grid = _make_grid(3, 6)
    all_cells = _ordered_cells(3, 6)
    outer = _ring_cells(3, 6, 0)
    grays = [(_gray_car(10, 0.0), 0, 0, 0.0), (_gray_car(11, 1.0), 0, 0, 1.0)]
    _place_grays(grid, grays, all_cells, outer, "estica")
    assert grid[0][3].id == 10
    white_cells = [(r, c) for r in range(3) for c in range(6)
                   if grid[r][c] and grid[r][c].id == 11]
    br, bc = white_cells[0]
    assert abs(br - 0) + abs(bc - 3) > 1  # não adjacente (espaçado)


def test_place_chroma_vazio_stays_off_perimeter():
    grid = _make_grid(3, 6)
    outer_set = set(_ring_cells(3, 6, 0))
    chroma = [(Car(id=1, cor_hex="#FF0000"), 0.0, 1.0, 1.0),
              (Car(id=2, cor_hex="#00FF00"), 0.33, 1.0, 1.0),
              (Car(id=3, cor_hex="#0000FF"), 0.66, 1.0, 1.0)]
    cfg = GradientConfig(sat_threshold_pct=0.0, partial_strategy="vazio",
                         interior_strategy="hue_value")
    _place_chroma(grid, chroma, 3, 6, outer_set, cfg)
    placed = [(r, c) for r in range(3) for c in range(6) if grid[r][c]]
    assert all(cell not in outer_set for cell in placed)


def test_grid_to_assignment_maps_to_real_slots():
    grid = _make_grid(1, 2)
    grid[0][0] = Car(id=1, cor_hex="#FF0000")
    grid[0][1] = Car(id=2, cor_hex="#00FF00")
    slot_map = {(0, 0): (1, 0, 0), (0, 1): (1, 0, 1)}
    res = _grid_to_assignment(grid, [grid[0][0], grid[0][1]], slot_map, 1, 2)
    assert res == {1: (1, 0, 0), 2: (1, 0, 1)}
