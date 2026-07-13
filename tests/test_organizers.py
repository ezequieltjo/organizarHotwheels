from models import Car, ShelfConfig, ParedeConfig
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        organize_favorites_first, total_slots, _fill_grid, _fill_wall_grid,
                        _is_gray)


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


# --- gray classification (critério composto: s + value) ---

def test_is_gray_neutral_pure_gray():
    assert _is_gray("#808080")  # cinza puro, s=0


def test_is_gray_dirty_gray_low_saturation():
    assert _is_gray("#8A8A8A")  # cinza sujo, saturação baixa


def test_is_gray_near_black():
    # vermelho quase preto: s alto mas v < 0.12 -> tratado como cinza escuro
    assert _is_gray("#0A0000")


def test_is_gray_near_white():
    # branco sujo: v > 0.92 e s < 0.30 -> cinza claro
    assert _is_gray("#F5F5F0")


def test_is_gray_pure_black_and_white():
    assert _is_gray("#000000")
    assert _is_gray("#FFFFFF")


def test_is_gray_chromatic_saturated_colors():
    assert not _is_gray("#FF0000")  # vermelho puro
    assert not _is_gray("#00FF00")  # verde puro
    assert not _is_gray("#FF8C00")  # laranja


def test_is_gray_navy_stays_chromatic():
    # azul marinho: v=0.5 (não é quase-preto), s alto -> cromático
    assert not _is_gray("#000080")


def test_is_gray_colored_dark_gray_blue():
    # cinza-azulado bem escuro (Batmóvel/GTR/Ice): dessaturado + escuro
    assert _is_gray("#262B33")


def test_is_gray_colored_olive_dark():
    # cinza-oliva escuro (Gemera)
    assert _is_gray("#5A5847")


def test_is_gray_colored_medium_light():
    # cinza colorido médio-claro (Speedtail, One-77): s baixo + v<0.70
    assert _is_gray("#9090B0")
    assert _is_gray("#90B090")


def test_is_gray_not_light_pastel():
    # pastel CLARO (lavanda/bege, v alto) continua cromático
    assert not _is_gray("#B0B0D0")


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
