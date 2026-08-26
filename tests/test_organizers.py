from models import Car, ShelfConfig, ParedeConfig, GradientConfig
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        organize_favorites_first, total_slots, _fill_grid, _fill_wall_grid,
                        _is_gray, _ring_cells, _ordered_cells,
                        _place_grays, _place_chroma, _grid_to_assignment, _ring_fill,
                        _split_overflow, _place_overflow_grays, _corner_segments,
                        _find_nearest_allowed)


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


def test_gradient_no_gray_all_chromatic():
    # sem cinzas: não quebra, todos no miolo
    cars = make_cars()
    shelves = [ShelfConfig(id=1, nome="P1", linhas=1, colunas=6)]
    result = organize_gradient(cars, shelves)
    assert len(result) == 3
    assert set(result.keys()) == {1, 2, 3}


def test_organize_gradient_with_config_smoke():
    cars = _neutrals(4) + [Car(id=1, cor_hex="#FF0000"), Car(id=2, cor_hex="#0000FF")]
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=6)]
    cfg = GradientConfig(sat_threshold_pct=10.0, partial_strategy="colorido",
                         interior_strategy="hue_value")
    res = organize_gradient(cars, shelves, config=cfg)
    assert len(res) == 6
    gray_cells = {res[c.id][1:] for c in _neutrals(4)}
    chroma_cells = {res[1][1:], res[2][1:]}
    assert gray_cells.isdisjoint(chroma_cells)


def test_organize_gradient_default_config():
    cars = [Car(id=1, cor_hex="#FF0000"), Car(id=2, cor_hex="#FFFFFF")]
    shelves = [ShelfConfig(id=1, nome="P1", linhas=2, colunas=4)]
    res = organize_gradient(cars, shelves)
    assert len(res) == 2


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
    """Without wall, ring fill still covers stacked shelves"""
    cars = make_cars()
    shelves = [
        ShelfConfig(id=1, nome="P1", linhas=1, colunas=1),
        ShelfConfig(id=2, nome="P2", linhas=1, colunas=2),
    ]
    result = organize_rainbow(cars, shelves, wall=None)
    assert len(result) == 3
    assert set(result.values()) == {(1, 0, 0), (2, 0, 0), (2, 0, 1)}


# --- ring placement helpers (Task 5) ---

def _make_grid(rows, cols):
    return [[None] * cols for _ in range(rows)]


def _gray_car(cid, value01):
    v = int(value01 * 255)
    return Car(id=cid, modelo=f"g{cid}", cor_hex=f"#{v:02X}{v:02X}{v:02X}")


def test_place_grays_fill_outer_ring_only():
    grid = _make_grid(3, 6)
    outer = _ring_cells(3, 6, 0)
    grays = [(_gray_car(10, 0.0), 0, 0, 0.0), (_gray_car(11, 1.0), 0, 0, 1.0)]
    _place_grays(grid, grays, outer, "colorido")
    assert grid[0][3].id == 10  # preto no seam_right (cols//2 = 3)
    assert grid[0][4].id == 11  # branco na próxima posição do anel


def test_place_grays_estica_spreads():
    # Após fix Task 9: endpoints cobrem o anel inteiro — preto em seam_right,
    # branco em seam_left (adjacentes por construção do anel).
    grid = _make_grid(3, 6)
    outer = _ring_cells(3, 6, 0)
    grays = [(_gray_car(10, 0.0), 0, 0, 0.0), (_gray_car(11, 1.0), 0, 0, 1.0)]
    _place_grays(grid, grays, outer, "estica")
    assert grid[0][3].id == 10            # preto em outer[0] = seam_right
    assert grid[0][2].id == 11            # branco em outer[-1] = seam_left


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


# --- _ring_fill integration ---

def _neutrals(n):
    """n carros neutros do preto (value 0) ao branco (value 1)."""
    out = []
    for i in range(n):
        v = int(255 * i / (n - 1)) if n > 1 else 128
        out.append(Car(id=100 + i, modelo=f"g{i}", cor_hex=f"#{v:02X}{v:02X}{v:02X}"))
    return out


def test_ring_fill_black_at_seam_white_adjacent_full_ring():
    # 3x6 perímetro = 14; preenche o anel inteiro
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=6)]
    grays = _neutrals(14)
    cfg = GradientConfig(sat_threshold_pct=5.0, partial_strategy="vazio")
    res = _ring_fill(grays, shelves, wall=None, disabled=None, cfg=cfg)
    black_id = 100                 # value 0 -> #000000
    white_id = 100 + 13            # value 1 -> #FFFFFF
    assert res[black_id][1:] == (0, 3)    # seam_right
    assert res[white_id][1:] == (0, 2)    # seam_left, adjacente


def test_ring_fill_concentric_overflow():
    shelves = [ShelfConfig(id=1, nome="P1", linhas=5, colunas=5)]
    grays = _neutrals(20)          # anel externo 5x5 = 16; 4 excedentes
    cfg = GradientConfig(sat_threshold_pct=5.0)
    res = _ring_fill(grays, shelves, wall=None, disabled=None, cfg=cfg)
    outer = set(_ring_cells(5, 5, 0))
    on_outer = sum(1 for _sid, r, c in res.values() if (r, c) in outer)
    assert on_outer == 16
    assert len(res) == 20


def test_ring_fill_overflow_routed_by_tone():
    # 5x5 anel = 16; excesso 4: 1 preto (i0), 2 cinzas medianos (i9, i10 —
    # janela central, tons ~0.47/0.53 próximos do canto inf-direito do anel
    # v~0.42; esquerdo é v~0.74), 1 branco (i19). Quinas coerentes com canto.
    shelves = [ShelfConfig(id=1, nome="P1", linhas=5, colunas=5)]
    grays = _neutrals(20)
    cfg = GradientConfig(sat_threshold_pct=5.0, partial_strategy="vazio")
    res = _ring_fill(grays, shelves, wall=None, disabled=None, cfg=cfg)
    outer = set(_ring_cells(5, 5, 0))
    assert res[119][1:] == (1, 1)  # branco mais claro: canto sup-esquerdo
    assert res[100][1:] == (1, 3)  # preto mais escuro: canto sup-direito
    assert res[109][1:] == (3, 3)  # mediano v~0.47: inf-direito (tom ~0.36)
    assert res[110][1:] == (3, 1)  # mediano v~0.53: inf-esquerdo (tom ~0.68)
    for i in (0, 9, 10, 19):
        assert res[100 + i][1:] not in outer


def test_split_overflow_proportional_balance():
    # Coleção real: muitos brancos, poucos pretos. Sem o split proporcional
    # só brancos transbordariam para as quinas.
    ring_cap = 30
    blacks = [(Car(id=i, cor_hex="#000000"), 0, 0, 0.0) for i in range(5)]
    mids = [(Car(id=100 + i, cor_hex="#808080"), 0, 0, 0.5) for i in range(10)]
    whites = [(Car(id=200 + i, cor_hex="#FFFFFF"), 0, 0, 1.0) for i in range(40)]
    grays = blacks + mids + whites  # 55 cinzas, anel 30 -> excesso 25
    ring, corners = _split_overflow(grays, ring_cap)
    assert len(ring) == 30 and len(corners) == 25
    corner_vals = [g[3] for g in corners]
    assert corner_vals.count(0.0) == round(25 * 5 / 55)     # pretos presentes
    assert corner_vals.count(1.0) == round(25 * 40 / 55)    # brancos presentes
    assert 0 < corner_vals.count(0.5)                       # cinzas presentes


def test_overflow_mids_match_corner_tone():
    # Cinzas médios vão para a quina inferior cujo tom do anel é o mais
    # próximo: ambos os cinzas (v~0.37) estão mais perto do canto direito
    # (v~0.35) que do esquerdo (v~0.70) — os dois agrupam à direita.
    grid = _make_grid(4, 6)
    grid[3][5] = Car(id=90, cor_hex="#595959")  # canto inf-direito, v~0.35
    grid[3][0] = Car(id=91, cor_hex="#B3B3B3")  # canto inf-esquerdo, v~0.70
    mids = [(_gray_car(80, 0.36), 0, 0, 0.36), (_gray_car(81, 0.38), 0, 0, 0.38)]
    _place_overflow_grays(grid, _corner_segments(grid, mids))
    assert grid[2][4].id == 80  # agrupados na diagonal da quina direita
    assert grid[2][5].id == 81
    assert grid[2][0] is None   # nada perto da quina esquerda


def test_chroma_never_closer_to_corner_than_gray():
    # Anel 16 (4x6) + 4 excedentes; 3 vermelhos escuros miram o canto
    # inf-esquerdo (hue 0 -> col 0, value baixo -> fundo). Células perto
    # da quina ficam reservadas aos cinzas: vermelho nunca mais perto da
    # ponta que o cinza da quina.
    shelves = [ShelfConfig(id=1, nome="P1", linhas=4, colunas=6)]
    grays = _neutrals(20)
    reds = [Car(id=1, cor_hex="#800000"), Car(id=2, cor_hex="#8B0000"),
            Car(id=3, cor_hex="#700000")]
    cfg = GradientConfig(sat_threshold_pct=5.0, partial_strategy="vazio")
    res = _ring_fill(grays + reds, shelves, wall=None, disabled=None, cfg=cfg)
    outer = set(_ring_cells(4, 6, 0))
    anchor = (3, 0)
    cheb = lambda p: max(abs(p[0] - anchor[0]), abs(p[1] - anchor[1]))
    corner_gray_ds = [cheb(res[100 + i][1:]) for i in range(20)
                      if res[100 + i][1:] not in outer]
    red_ds = [cheb(res[cid][1:]) for cid in (1, 2, 3)]
    assert min(red_ds) > min(corner_gray_ds)


def test_organize_rainbow_gray_moldura():
    # 3x6: 14 cinzas enchem o anel; coloridos por hue no miolo (row-major).
    grays = _neutrals(14)
    chroma = [Car(id=1, cor_hex="#0000FF"),  # hue 0.67
              Car(id=2, cor_hex="#FF0000"),  # hue 0.0
              Car(id=3, cor_hex="#00FF00")]  # hue 0.33
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=6)]
    res = organize_rainbow(grays + chroma, shelves)
    outer = set(_ring_cells(3, 6, 0))
    for i in range(14):
        assert res[100 + i][1:] in outer
    assert res[2][1:] == (1, 1)  # vermelho (hue 0) primeiro no miolo
    assert res[3][1:] == (1, 2)  # verde
    assert res[1][1:] == (1, 3)  # azul


def test_ring_fill_partial_colorido_puts_chroma_on_perimeter():
    grays = _neutrals(1)
    chroma = [Car(id=i, cor_hex=h) for i, h in
              [(i, f"#{(i * 40) % 256:02X}0000") for i in range(1, 11)]]
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=6)]
    cfg = GradientConfig(sat_threshold_pct=5.0, partial_strategy="colorido")
    res = _ring_fill(grays + chroma, shelves, wall=None, disabled=None, cfg=cfg)
    outer = set(_ring_cells(3, 6, 0))
    on_outer = sum(1 for cid in range(1, 11) if res[cid][1:] in outer)
    assert on_outer > 0


def test_ring_fill_partial_vazio_keeps_chroma_off_perimeter():
    grays = _neutrals(1)
    chroma = [Car(id=1, cor_hex="#FF0000"), Car(id=2, cor_hex="#00FF00"),
              Car(id=3, cor_hex="#0000FF")]
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=6)]
    cfg = GradientConfig(sat_threshold_pct=5.0, partial_strategy="vazio")
    res = _ring_fill(grays + chroma, shelves, wall=None, disabled=None, cfg=cfg)
    outer = set(_ring_cells(3, 6, 0))
    for cid in (1, 2, 3):
        assert res[cid][1:] not in outer


def test_ring_fill_interior_similaridade_groups_reds():
    chroma = [Car(id=1, cor_hex="#FF0000"), Car(id=2, cor_hex="#FF1010"),
              Car(id=3, cor_hex="#0000FF")]
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=6)]
    cfg = GradientConfig(sat_threshold_pct=0.0, interior_strategy="similaridade")
    res = _ring_fill(chroma, shelves, wall=None, disabled=None, cfg=cfg)
    p1, p2 = res[1][1:], res[2][1:]
    assert abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]) <= 2


def test_ring_fill_no_grays():
    chroma = [Car(id=1, cor_hex="#FF0000"), Car(id=2, cor_hex="#00FF00"),
              Car(id=3, cor_hex="#0000FF")]
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=6)]
    res = _ring_fill(chroma, shelves, wall=None, disabled=None,
                     cfg=GradientConfig())
    assert len(res) == 3


def test_ring_fill_respects_disabled():
    grays = _neutrals(3)
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=6)]
    disabled = {1: {"rows": [], "cells": [(0, 3)]}}  # bloqueia seam preto
    cfg = GradientConfig(sat_threshold_pct=5.0)
    res = _ring_fill(grays, shelves, wall=None, disabled=disabled, cfg=cfg)
    assert (1, 0, 3) not in res.values()


# --- edge-case coverage gaps (Task 9: deferred from T5/T6 reviews) ---

def test_ring_fill_degenerate_single_row():
    # M1 (T6 review): 1-row shelf falls back to all_cells as outer_ring.
    cars = [Car(id=1, cor_hex="#FF0000"), Car(id=2, cor_hex="#000000"),
            Car(id=3, cor_hex="#FFFFFF")]
    shelves = [ShelfConfig(id=1, nome="P1", linhas=1, colunas=4)]
    cfg = GradientConfig(sat_threshold_pct=5.0)
    res = _ring_fill(cars, shelves, wall=None, disabled=None, cfg=cfg)
    assert len(res) == 3
    assert set(res.keys()) == {1, 2, 3}


def test_ring_fill_partial_estica_spreads():
    # M2 (T6 review) + fix Task 9: grays distribuídos no anel; preto em
    # seam_right e branco em seam_left (sempre adjacentes por construção).
    # O cinza do meio deve ficar fora desse par adjacente.
    grays = _neutrals(3)  # black, mid, white
    shelves = [ShelfConfig(id=1, nome="P1", linhas=3, colunas=6)]
    cfg = GradientConfig(sat_threshold_pct=5.0, partial_strategy="estica")
    res = _ring_fill(grays, shelves, wall=None, disabled=None, cfg=cfg)
    outer = set(_ring_cells(3, 6, 0))
    black_pos = res[grays[0].id][1:]
    mid_pos = res[grays[1].id][1:]
    white_pos = res[grays[2].id][1:]
    assert all(p in outer for p in (black_pos, mid_pos, white_pos))
    assert black_pos == (0, 3)  # seam_right
    assert white_pos == (0, 2)  # seam_left
    # middle gray must NOT be adjacent to either endpoint
    assert (abs(mid_pos[0] - black_pos[0]) + abs(mid_pos[1] - black_pos[1])) > 1
    assert (abs(mid_pos[0] - white_pos[0]) + abs(mid_pos[1] - white_pos[1])) > 1


def test_grid_to_assignment_fallback_to_nearest_real_slot():
    # Deferred from T5 review: a grid cell not in slot_map triggers
    # _find_nearest_real_slot.
    grid = [[None, None, None]]
    grid[0][0] = Car(id=1, cor_hex="#FF0000")
    grid[0][2] = Car(id=2, cor_hex="#00FF00")  # col 2 NOT in slot_map
    slot_map = {(0, 0): (1, 0, 0), (0, 1): (1, 0, 1)}  # only cols 0,1 are real
    res = _grid_to_assignment(grid, [grid[0][0], grid[0][2]], slot_map, 1, 3)
    assert res[1] == (1, 0, 0)
    assert res[2] == (1, 0, 1)  # nearest real slot to (0,2) is (0,1)


# --- Final-review fixes (Task 9): search radius, miolo-first, estica endpoints ---

def test_find_nearest_allowed_reaches_far_corner():
    # 4x4 grid, only (0,0) allowed; target (3,3) tem Manhattan 6 = (R-1)+(C-1).
    # Antes do fix o raio era max(R,C)-1 = 3 e (0,0) ficava inalcançável.
    grid = _make_grid(4, 4)
    allowed = {(0, 0)}
    assert _find_nearest_allowed(grid, 3, 3, allowed, 4, 4) == (0, 0)


def test_place_chroma_hue_value_miolo_first():
    # 3x6 grid, 1 cinza + 4 cromos (capacidade do miolo = 4).
    # partial_strategy=colorido: todos os cromos devem ir para o miolo.
    grid = _make_grid(3, 6)
    grid[0][3] = _gray_car(10, 0.0)  # cinza occupy seam_right
    outer_set = set(_ring_cells(3, 6, 0))
    chroma = [(Car(id=i, cor_hex=h), h_idx / 4.0, 1.0, 1.0)
              for i, (h, h_idx) in enumerate(
                  [("#FF0000", 0), ("#00FF00", 1), ("#0000FF", 2), ("#FFFF00", 3)],
                  start=1)]
    cfg = GradientConfig(sat_threshold_pct=0.0, partial_strategy="colorido",
                         interior_strategy="hue_value")
    _place_chroma(grid, chroma, 3, 6, outer_set, cfg)
    placed = [(r, c) for r in range(3) for c in range(6)
              if grid[r][c] and grid[r][c].id in (1, 2, 3, 4)]
    assert len(placed) == 4
    assert all(cell not in outer_set for cell in placed)


def test_place_grays_estica_white_at_seam():
    # 3x6 (anel 14 células); 3 cinzas (preto, mid, branco).
    # Branco (value alto) deve ir para outer_ring[-1] = seam_left (0,2);
    # preto (value baixo) para outer_ring[0] = seam_right (0,3).
    grid = _make_grid(3, 6)
    outer = _ring_cells(3, 6, 0)
    grays = [(_gray_car(10, 0.0), 0, 0, 0.0),
             (_gray_car(11, 0.5), 0, 0, 0.5),
             (_gray_car(12, 1.0), 0, 0, 1.0)]
    _place_grays(grid, grays, outer, "estica")
    assert outer[0] == (0, 3)
    assert outer[-1] == (0, 2)
    assert grid[0][3].id == 10  # preto no seam_right
    assert grid[0][2].id == 12  # branco no seam_left
