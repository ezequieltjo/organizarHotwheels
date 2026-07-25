# Degradê Moldura de Cinza — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar o modo Degradê para dispor os carros cinza como uma moldura (anel horário preto→branco) ao redor dos coloridos, com 3 controles (slider de % saturação, estratégia de anel parcial, estratégia de miolo) e re-rodar automático.

**Architecture:** `GradientConfig` dataclass imutável agrupa os 3 parâmetros, threaded só em `organize_gradient`. Algoritmo do anel (`_ring_fill`) reusa `_build_slot_list`/`_hex_to_hsv`/`_nearest_neighbor_sort` e mapeia a grade virtual para slots reais. UI Streamlit mostra os controles só no modo Degradê e regenera o assignment ao mudá-los.

**Tech Stack:** Python 3, Streamlit, pytest, colorsys (stdlib), dataclasses.

## Global Constraints

- Classificação de cinza = **único limiar de saturação HSV** (`s <= limiar`), substituindo as 4 regras antigas. Escala 0–1 internamente; UI em % (0–50, default 12).
- Seam do anel no **centro do topo**: preto em `(0, cols//2)`, branco termina adjacente em `(0, cols//2-1)` quando o anel fecha.
- Sentido **horário**: topo direita → borda direita ↓ → fundo ← → borda esquerda ↑ → topo esquerda.
- Estratégias válidas: `partial_strategy` ∈ `{colorido, vazio, estica}`; `interior_strategy` ∈ `{hue_value, similaridade}`.
- Imutabilidade: `GradientConfig` é `frozen=True`. Nenhum mutation de objetos `Car` existentes.
- PEP 8, type annotations em todas as assinaturas novas.
- Cobertura ≥ 80% no código novo/modificado.
- Não quebrar os outros modos (arco-íris, marca, etc.) nem a UI de coleção/expositores.

**Spec:** `docs/superpowers/specs/2026-07-25-degrade-moldura-cinza-design.md`

---

## File Structure

- `models.py` — adicionar `GradientConfig` (frozen dataclass).
- `organizers.py` — refatorar `_is_gray` (limiar de saturação), remover constantes HSV antigas, adicionar `_ring_cells`, `_ordered_cells`, `_place_grays`, `_place_chroma`, `_find_nearest_allowed`, `_grid_to_assignment`, `_ring_fill`; reescrever `organize_gradient`; remover `_gradient_2d_fill`.
- `app.py` — renomear entrada `ORGANIZERS`, adicionar 3 controles + auto re-rodar, importar `GradientConfig`.
- `tests/test_organizers.py` — reescrever bloco `test_is_gray_*`, remover testes de layout lateral antigo, adicionar testes do anel.

---

## Task 1: `GradientConfig` dataclass

**Files:**
- Modify: `models.py` (adicionar após `ParedeConfig`)
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `models.GradientConfig` com campos `sat_threshold_pct: float = 12.0`, `partial_strategy: str = "colorido"`, `interior_strategy: str = "hue_value"`.

- [ ] **Step 1: Write the failing test**

Adicionar em `tests/test_models.py`:

```python
from models import GradientConfig


def test_gradient_config_defaults():
    cfg = GradientConfig()
    assert cfg.sat_threshold_pct == 12.0
    assert cfg.partial_strategy == "colorido"
    assert cfg.interior_strategy == "hue_value"


def test_gradient_config_is_frozen():
    import dataclasses
    cfg = GradientConfig()
    try:
        cfg.sat_threshold_pct = 50.0  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("GradientConfig deve ser imutável (frozen)")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL com `ImportError: cannot import name 'GradientConfig'`

- [ ] **Step 3: Write minimal implementation**

Adicionar no final de `models.py`:

```python
@dataclass(frozen=True)
class GradientConfig:
    """Parâmetros do modo Degradê (moldura de cinza)."""
    sat_threshold_pct: float = 12.0       # 0-50
    partial_strategy: str = "colorido"    # colorido | vazio | estica
    interior_strategy: str = "hue_value"  # hue_value | similaridade
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (todos os testes de models, incluindo os 2 novos)

- [ ] **Step 5: Commit**

```bash
git add models.py tests/test_models.py
git commit -m "feat: add GradientConfig dataclass for degradê mode"
```

---

## Task 2: Refatorar `_is_gray` para limiar de saturação puro

**Files:**
- Modify: `organizers.py:7-13` (remover constantes), `organizers.py:175-186` (`_is_gray`), `organizers.py:204` (chamada em `_gradient_2d_fill`)
- Test: `tests/test_organizers.py:112-166` (reescrever bloco `test_is_gray_*`)

**Interfaces:**
- Produces: `_is_gray(hex_color: str, sat_threshold: float) -> bool` (sat_threshold em escala 0–1, sem default).
- Consumes: `_hex_to_hsv` (existente, mantido).
- Temporário neste task: `_gradient_2d_fill` passa `0.12` explicitamente (removido no Task 7 junto com a função).

- [ ] **Step 1: Write the failing tests (reescrever bloco)**

Substituir TODO o bloco de `test_is_gray_neutral_pure_gray` até `test_is_gray_not_light_pastel` (linhas ~112–166) por:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_organizers.py -k is_gray -v`
Expected: FAIL — `_is_gray()` recebe 1 arg mas a assinatura atual exige a mudança; ou asserções de `#0A0000`/`#9090B0` falham com a regra antiga.

- [ ] **Step 3: Implement — remover constantes, refatorar `_is_gray`, atualizar chamada temporária**

Em `organizers.py`, **remover** as linhas 7–13 (bloco de constantes `GRAY_SAT_THRESHOLD` … `COLORED_GRAY_MAX_SAT`).

Substituir a função `_is_gray` (linhas ~175–186) por:

```python
def _is_gray(hex_color: str, sat_threshold: float) -> bool:
    """True se saturação HSV <= sat_threshold (escala 0-1).

    Preto, branco e cinzas neutros (sat ~ 0) sempre contam como cinza.
    """
    _, s, _ = _hex_to_hsv(hex_color)
    return s <= sat_threshold
```

Em `_gradient_2d_fill`, atualizar a chamada (linha ~204) de `if _is_gray(car.cor_hex):` para `if _is_gray(car.cor_hex, 0.12):` (temporário — esta função é removida no Task 7).

- [ ] **Step 4: Run full suite to verify it passes**

Run: `pytest tests/test_organizers.py -v`
Expected: PASS — `test_is_gray_*` novos passam; `test_gradient_gray_*` (layout lateral antigo) ainda passam pois usam cores neutras e a lógica de layout não mudou.

- [ ] **Step 5: Commit**

```bash
git add organizers.py tests/test_organizers.py
git commit -m "refactor: classify gray by pure saturation threshold"
```

---

## Task 3: Helper `_ring_cells` (perímetro horário com seam)

**Files:**
- Modify: `organizers.py` (adicionar função)
- Test: `tests/test_organizers.py` (adicionar testes + import)

**Interfaces:**
- Produces: `_ring_cells(rows: int, cols: int, offset: int = 0) -> list[tuple[int, int]]`.
- Requer `rows >= 2` e `cols >= 2`. Lista sem duplicatas. Primeiro elemento `(offset, offset + cols//2)` (preto); último `(offset, offset + cols//2 - 1)` (branco).

- [ ] **Step 1: Write the failing tests**

Adicionar import no topo de `tests/test_organizers.py` (linha 2–5), incluir `_ring_cells` na importação de `organizers`:

```python
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        organize_favorites_first, total_slots, _fill_grid, _fill_wall_grid,
                        _is_gray, _ring_cells)
```

Adicionar testes (após o bloco `test_is_gray_*`):

```python
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
    inner = _ring_cells(5, 5, 1)   # anel interno 3x3 com offset 1
    assert (1, 1) in inner
    assert set(outer).isdisjoint(set(inner))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_organizers.py -k ring_cells -v`
Expected: FAIL com `ImportError: cannot import name '_ring_cells'`

- [ ] **Step 3: Implement**

Adicionar em `organizers.py` (após `_is_gray`):

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_organizers.py -k ring_cells -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add organizers.py tests/test_organizers.py
git commit -m "feat: add clockwise ring perimeter helper"
```

---

## Task 4: Helper `_ordered_cells` (anéis concêntricos)

**Files:**
- Modify: `organizers.py` (adicionar função)
- Test: `tests/test_organizers.py`

**Interfaces:**
- Produces: `_ordered_cells(rows: int, cols: int) -> list[tuple[int, int]]` — todas as células, anel externo primeiro (horário), depois anéis internos, miolo final em row-major. Sem duplicatas. Segura para `rows, cols >= 1`.
- Consumes: `_ring_cells` (Task 3).

- [ ] **Step 1: Write the failing tests**

Adicionar `_ordered_cells` ao import de `organizers` em `tests/test_organizers.py`. Adicionar testes:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_organizers.py -k ordered_cells -v`
Expected: FAIL com `ImportError: cannot import name '_ordered_cells'`

- [ ] **Step 3: Implement**

Adicionar em `organizers.py` (após `_ring_cells`):

```python
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
        cells.extend(_ring_cells(rows, cols, offset))
        offset += 1
    return list(dict.fromkeys(cells))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_organizers.py -k ordered_cells -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add organizers.py tests/test_organizers.py
git commit -m "feat: add concentric ordered cells helper"
```

---

## Task 5: Helpers de posicionamento (`_place_grays`, `_place_chroma`, `_find_nearest_allowed`, `_grid_to_assignment`)

**Files:**
- Modify: `organizers.py` (adicionar funções)
- Test: `tests/test_organizers.py`

**Interfaces:**
- Produces:
  - `_place_grays(grid, grays, all_cells, outer_ring, strategy) -> None`
  - `_place_chroma(grid, chroma, total_rows, total_cols, outer_set, cfg) -> None`
  - `_find_nearest_allowed(grid, row, col, allowed, total_rows, total_cols) -> tuple[int,int] | None`
  - `_grid_to_assignment(grid, cars, slot_map, total_rows, total_cols) -> dict`
- Consumes: `_ring_cells`, `_ordered_cells`, `_is_gray`, `_nearest_neighbor_sort`, `_find_nearest_empty`, `_find_nearest_real_slot` (existentes), `GradientConfig`.

- [ ] **Step 1: Write the failing tests**

Adicionar imports `_place_grays, _place_chroma, _grid_to_assignment` ao import de `organizers`. Adicionar `from models import GradientConfig` no topo (se ainda não importado). Adicionar testes:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_organizers.py -k "place_grays or place_chroma or grid_to_assignment" -v`
Expected: FAIL com `ImportError`.

- [ ] **Step 3: Implement**

Atualizar import no topo de `organizers.py`:

```python
from models import Car, ShelfConfig, ParedeConfig, GradientConfig
```

Adicionar em `organizers.py` (após `_ordered_cells`):

```python
def _find_nearest_allowed(grid, row, col, allowed, total_rows, total_cols):
    """Célula vazia mais próxima de (row, col) dentro do conjunto permitido."""
    if (row, col) in allowed:
        return (row, col)
    for dist in range(1, max(total_rows, total_cols)):
        for dr in range(-dist, dist + 1):
            for dc in range(-dist, dist + 1):
                if abs(dr) + abs(dc) != dist:
                    continue
                cell = (row + dr, col + dc)
                if cell in allowed:
                    return cell
    return None


def _place_grays(grid, grays, all_cells, outer_ring, strategy):
    """Posiciona cinzas (já ordenados preto->branco) no anel.

    estica (e poucos cinzas): distribui uniformemente pelo anel externo.
    caso geral: preenche anel externo e depois anéis internos (concêntrico).
    """
    if not grays:
        return
    rows, cols = len(grid), len(grid[0])
    n = len(grays)
    if strategy == "estica" and n < len(outer_ring):
        step = max(1, len(outer_ring) // n)
        for i, (car, _h, _s, _v) in enumerate(grays):
            idx = min(i * step, len(outer_ring) - 1)
            r, c = outer_ring[idx]
            if grid[r][c] is None:
                grid[r][c] = car
            else:
                er, ec = _find_nearest_empty(grid, r, c, rows, cols)
                if er is not None:
                    grid[er][ec] = car
        return
    for (car, _h, _s, _v), (r, c) in zip(grays, all_cells):
        if grid[r][c] is None:
            grid[r][c] = car
        else:
            er, ec = _find_nearest_empty(grid, r, c, rows, cols)
            if er is not None:
                grid[er][ec] = car


def _place_chroma(grid, chroma, total_rows, total_cols, outer_set, cfg):
    """Posiciona coloridos no miolo (e perímetro, conforme estratégia)."""
    if not chroma:
        return
    allowed = {(r, c) for r in range(total_rows) for c in range(total_cols)
               if grid[r][c] is None}
    if cfg.partial_strategy == "vazio":
        allowed = {cell for cell in allowed if cell not in outer_set}

    if cfg.interior_strategy == "similaridade":
        ordered = _nearest_neighbor_sort([c[0] for c in chroma])
        interior = sorted(cell for cell in allowed if cell not in outer_set)
        perimeter = sorted(cell for cell in allowed if cell in outer_set)
        seq = interior + perimeter
        for car, cell in zip(ordered, seq):
            grid[cell[0]][cell[1]] = car
            allowed.discard(cell)
        return

    for car, h, _s, v in chroma:
        target_col = int(h * total_cols) % total_cols
        target_row = int((1.0 - v) * total_rows) if total_rows > 1 else 0
        target_row = min(max(target_row, 0), total_rows - 1)
        cell = _find_nearest_allowed(grid, target_row, target_col, allowed,
                                     total_rows, total_cols)
        if cell is not None:
            grid[cell[0]][cell[1]] = car
            allowed.discard(cell)


def _grid_to_assignment(grid, cars, slot_map, total_rows, total_cols):
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
    remaining_cars = [c for c in cars if c.id not in assignment]
    remaining_slots = [pos for pos in slot_map if pos not in used]
    for car, pos in zip(remaining_cars, remaining_slots):
        assignment[car.id] = slot_map[pos]
        used.add(pos)
    return assignment
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_organizers.py -k "place_grays or place_chroma or grid_to_assignment" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add organizers.py tests/test_organizers.py
git commit -m "feat: add ring placement helpers (grays, chroma, assignment)"
```

---

## Task 6: `_ring_fill` (orquestrador) + testes de integração do anel

**Files:**
- Modify: `organizers.py` (adicionar `_ring_fill`)
- Test: `tests/test_organizers.py`

**Interfaces:**
- Produces: `_ring_fill(cars, shelves, wall, disabled, cfg) -> dict`.
- Consumes: `_build_slot_list`, `_hex_to_hsv`, `_is_gray`, `_ring_cells`, `_ordered_cells`, `_place_grays`, `_place_chroma`, `_grid_to_assignment`, `GradientConfig`.

- [ ] **Step 1: Write the failing tests**

Adicionar `_ring_fill` ao import de `organizers`. Adicionar testes:

```python
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
    grays = _neutrals(20)          # anel externo 5x5 = 16; 4 no interno
    cfg = GradientConfig(sat_threshold_pct=5.0)
    res = _ring_fill(grays, shelves, wall=None, disabled=None, cfg=cfg)
    outer = set(_ring_cells(5, 5, 0))
    on_outer = sum(1 for _sid, r, c in res.values() if (r, c) in outer)
    assert on_outer == 16
    assert len(res) == 20


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_organizers.py -k ring_fill -v`
Expected: FAIL com `ImportError: cannot import name '_ring_fill'`.

- [ ] **Step 3: Implement**

Adicionar em `organizers.py` (após `_grid_to_assignment`):

```python
def _ring_fill(cars, shelves, wall, disabled, cfg):
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
    all_cells = [c for c in _ordered_cells(total_rows, total_cols) if c in slot_map]
    if total_rows >= 2 and total_cols >= 2:
        outer_ring = [c for c in _ring_cells(total_rows, total_cols, 0) if c in slot_map]
    else:
        outer_ring = list(all_cells)
    outer_set = set(outer_ring)

    _place_grays(grid, grays, all_cells, outer_ring, cfg.partial_strategy)
    _place_chroma(grid, chroma, total_rows, total_cols, outer_set, cfg)

    return _grid_to_assignment(grid, cars, slot_map, total_rows, total_cols)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_organizers.py -k ring_fill -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add organizers.py tests/test_organizers.py
git commit -m "feat: add ring fill orchestrator for degradê frame layout"
```

---

## Task 7: Conectar `organize_gradient` ao `_ring_fill`, remover `_gradient_2d_fill`

**Files:**
- Modify: `organizers.py:39-44` (`organize_gradient`), remover `_gradient_2d_fill` (~189–280)
- Test: `tests/test_organizers.py` (remover testes de layout lateral antigo, adicionar teste de smoke do modo)

**Interfaces:**
- Produces: `organize_gradient(cars, shelves, wall=None, disabled=None, config=None) -> dict`.
- Remove: `_gradient_2d_fill` e a chamada temporária `_is_gray(car.cor_hex, 0.12)`.

- [ ] **Step 1: Write the updated tests**

Em `tests/test_organizers.py`, **remover** as funções `test_gradient_gray_on_lateral_columns`, `test_gradient_gray_light_left_dark_right`, `test_gradient_gray_vertical_light_to_dark` (linhas ~182–224) — elas testam o layout lateral antigo. Manter `test_organize_gradient` e `test_gradient_no_gray_all_chromatic`.

Adicionar testes de smoke do modo completo:

```python
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
```

- [ ] **Step 2: Run tests to verify current state**

Run: `pytest tests/test_organizers.py -v`
Expected: os testes de layout lateral removidos somem; os smoke tests podem PASSAR ou o `isdisjoint` pode falhar com o layout antigo — a Step 3 conserta o comportamento.

- [ ] **Step 3: Implement — reescrever `organize_gradient`, remover `_gradient_2d_fill`**

Substituir `organize_gradient` (linhas ~39–44) por:

```python
def organize_gradient(cars: list[Car], shelves: list[ShelfConfig],
                      wall: ParedeConfig = None, disabled: dict | None = None,
                      config: GradientConfig | None = None) -> dict:
    cars = _filter_reserva(cars)
    if not cars:
        return {}
    cfg = config or GradientConfig()
    return _ring_fill(cars, shelves, wall, disabled, cfg)
```

**Remover** toda a função `_gradient_2d_fill` (linhas ~189–280). Permanecem as helpers reaproveitadas: `_build_slot_list`, `_find_nearest_real_slot`, `_find_nearest_empty`, `_hex_to_hsv`, `_nearest_neighbor_sort`.

- [ ] **Step 4: Run full suite to verify it passes**

Run: `pytest tests/test_organizers.py -v`
Expected: PASS — todos os testes do anel + smoke; nenhum teste de layout lateral resta.

- [ ] **Step 5: Commit**

```bash
git add organizers.py tests/test_organizers.py
git commit -m "refactor: wire degradê mode to ring fill, drop legacy gradient layout"
```

---

## Task 8: UI — controles do Degradê + auto re-rodar (`app.py`)

**Files:**
- Modify: `app.py:5` (import `GradientConfig`), `app.py:27` (rename `ORGANIZERS`), `app.py:497-538` (aba Organizar)
- Test: verificação manual + smoke de import

**Interfaces:**
- Consumes: `organize_gradient(..., config=cfg)`, `GradientConfig`.

- [ ] **Step 1: Atualizar imports e rename**

Em `app.py:5`, trocar:
```python
from models import Car, ShelfConfig, ParedeConfig
```
por:
```python
from models import Car, ShelfConfig, ParedeConfig, GradientConfig
```

Em `app.py:27`, trocar:
```python
    "Degradê (similaridade)": organize_gradient,
```
por:
```python
    "Degradê (moldura)": organize_gradient,
```

- [ ] **Step 2: Substituir o bloco da aba Organizar**

Substituir o trecho de `modo = st.selectbox("Modo de organização", ...)` até o final do bloco `if "assignment" in st.session_state and st.session_state.assignment:` (linhas ~497–538) por:

```python
        modo = st.selectbox("Modo de organização", list(ORGANIZERS.keys()))

        # Controles exclusivos do modo Degradê (moldura)
        deg_cfg = None
        if modo.startswith("Degradê"):
            dsat = st.slider("Saturação máx p/ cinza (%)", 0, 50, 12, key="deg_sat")
            partial_opts = {"Colorido preenche": "colorido",
                            "Vagas vazias": "vazio",
                            "Estica gradiente": "estica"}
            interior_opts = {"Hue+value": "hue_value",
                             "Similaridade": "similaridade"}
            dpartial = st.selectbox("Anel parcial", list(partial_opts), key="deg_partial")
            dinterior = st.selectbox("Miolo colorido", list(interior_opts), key="deg_interior")
            deg_cfg = GradientConfig(
                sat_threshold_pct=float(dsat),
                partial_strategy=partial_opts[dpartial],
                interior_strategy=interior_opts[dinterior],
            )

        if st.button("Gerar organização"):
            func = ORGANIZERS[modo]
            if deg_cfg is not None and func is organize_gradient:
                assignment = func(cars, shelves, wall, disabled, config=deg_cfg)
            else:
                assignment = func(cars, shelves, wall, disabled)
            st.session_state.assignment = assignment
            st.rerun()

        # Auto re-rodar ao mexer nos controles do Degradê
        if deg_cfg is not None and st.session_state.get("assignment"):
            st.session_state.assignment = organize_gradient(
                cars, shelves, wall, disabled, config=deg_cfg)

        if "assignment" in st.session_state and st.session_state.assignment:
            assignment = st.session_state.assignment
            fig = render_grid(assignment, cars, shelves, wall, disabled)
            st.plotly_chart(fig, width="stretch", key="grid_organizar")

            st.subheader("Posições")
            car_map = {c.id: c for c in cars}
            pos_data = []
            for car_id, (shelf_id, row, col) in assignment.items():
                car = car_map.get(car_id)
                if car:
                    shelf = next((s for s in shelves if s.id == shelf_id), None)
                    pos_data.append({
                        "Modelo": car.modelo,
                        "Cor": car.cor,
                        "Expositor": shelf.nome if shelf else "?",
                        "Linha": row + 1,
                        "Coluna": col + 1,
                    })
            st.dataframe(pos_data, width="stretch", hide_index=True)

            c1, c2 = st.columns(2)
            if c1.button("Aplicar posições"):
                clear_positions()
                apply_positions(assignment)
                refresh()
                del st.session_state.assignment
                st.success("Posições salvas!")
                st.rerun()
            if c2.button("Exportar CSV"):
                import pandas as pd
                df = pd.DataFrame(pos_data)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Baixar", csv, "organizacao.csv", "text/csv")
```

- [ ] **Step 3: Smoke test de import/sintaxe**

Run: `python -c "import ast; ast.parse(open('app.py').read()); print('ok')"`
Expected: imprime `ok` (sintaxe válida).

- [ ] **Step 4: Verificação manual**

Run: `streamlit run app.py` (ou `./rodar.sh`).
Expected:
- Aba **Organizar** → selecionar "Degradê (moldura)" → aparecem 3 controles (slider 0–50, 2 seletores).
- Com expositor 3×6 e coleção carregada, clicar "Gerar organização" → cinzas formam o anel (preto no centro-direita do topo), coloridos no miolo.
- Mover o slider de saturação → grade regenera sozinha (auto re-rodar).
- Trocar "Anel parcial" e "Miolo colorido" → regenera.
- Selecionar outro modo (ex.: Arco-íris) → controles somem, funciona normalmente.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: degradê frame UI with saturation slider and auto re-run"
```

---

## Task 9: Cobertura, limpeza e verificação final

**Files:**
- Verify: `organizers.py`, `models.py`, `tests/`
- Modify: conforme gaps de cobertura

- [ ] **Step 1: Rodar cobertura**

Run: `pytest --cov=organizers --cov=models --cov-report=term-missing tests/`
Expected: cobertura ≥ 80% em `organizers.py` e `models.py`. Anotar linhas não cobertas.

- [ ] **Step 2: Preencher lacunas de cobertura (se houver)**

Adicionar testes em `tests/test_organizers.py` para ramos não cobertos (ex.: `_find_nearest_allowed` sem célula permitida, `_place_grays` com célula ocupada caindo em `_find_nearest_empty`, `_grid_to_assignment` com slot virtual fora do `slot_map`). Seguir padrão AAA.

- [ ] **Step 3: Rodar suite completa**

Run: `pytest -v`
Expected: todos os testes PASS.

- [ ] **Step 4: Lint rápido**

Run: `python -m py_compile organizers.py app.py models.py`
Expected: sem erros de sintaxe. (Opcional: `ruff check organizers.py models.py` se disponível.)

- [ ] **Step 5: Commit final**

```bash
git add tests/test_organizers.py
git commit -m "test: cover ring fill edge cases for degradê frame"
```

---

## Self-Review

- [ ] Spec coverage: cada requisito do spec (anel horário, seam, 3 controles, auto re-rodar, concêntrico, 3 estratégias parciais, 2 miolos, casos extremos) tem task correspondente.
- [ ] Sem placeholders (TBD/TODO/"implement later").
- [ ] Tipos consistentes: `_is_gray(hex_color, sat_threshold)`, `_ring_cells(rows, cols, offset)`, `_ring_fill(..., cfg)` usam os mesmos nomes em todos os tasks.
- [ ] Suíte verde após cada task.
