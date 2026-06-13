# Vagas bloqueadas em expositores

**Data:** 2026-06-13
**Status:** Design

## Contexto

Coleção tem 162 carros, mas apenas 160 cabem no organizador físico. As últimas 4 linhas dos 2 expositores de baixo estão livres (40 vagas não usadas). Hoje o algoritmo de organização considera todas as `linhas × colunas` como vagas disponíveis, então ocupa posições que fisicamente não devem receber carros.

## Objetivo

Permitir marcar vagas (por linha inteira ou célula individual) como bloqueadas. O algoritmo de organização deve pular essas vagas ao posicionar carros, considerando apenas as vagas realmente disponíveis.

## Escopo

- Bloqueio por linha inteira (caso primário)
- Bloqueio por célula individual (caso secundário)
- Configuração via form por expositor na aba Expositores
- Visualização distinta das vagas bloqueadas na grade de preview
- Backward compatible: nenhum bloqueio por padrão

Fora de escopo: bloqueio por coluna inteira, bloqueio temporário por sessão, importação/exportação de bloqueios.

## Modelo de dados

Nova tabela:

```sql
CREATE TABLE IF NOT EXISTS disabled_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shelf_id INTEGER NOT NULL,
    posicao_linha INTEGER NOT NULL,
    posicao_coluna INTEGER,   -- NULL = linha inteira bloqueada
    UNIQUE(shelf_id, posicao_linha, posicao_coluna),
    FOREIGN KEY(shelf_id) REFERENCES shelf_configs(id) ON DELETE CASCADE
);
```

- `posicao_coluna IS NULL` representa bloqueio de linha inteira
- `posicao_coluna NOT NULL` representa bloqueio de célula individual
- Cascade delete garante limpeza quando shelf é removida
- Tabela começa vazia → comportamento atual inalterado

`init_db()` ganha `CREATE TABLE IF NOT EXISTS disabled_slots`. Sem migração de dados.

## Storage layer (`storage.py`)

Novas funções:

```python
def get_disabled_slots(shelf_id: int) -> dict:
    """Returns {'rows': set[int], 'cells': set[tuple[int,int]]}."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT posicao_linha, posicao_coluna FROM disabled_slots WHERE shelf_id=?",
        (shelf_id,)).fetchall()
    conn.close()
    out = {"rows": set(), "cells": set()}
    for r in rows:
        if r["posicao_coluna"] is None:
            out["rows"].add(r["posicao_linha"])
        else:
            out["cells"].add((r["posicao_linha"], r["posicao_coluna"]))
    return out


def get_all_disabled_slots() -> dict[int, dict]:
    """Returns {shelf_id: {'rows': set, 'cells': set}}."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT shelf_id, posicao_linha, posicao_coluna FROM disabled_slots").fetchall()
    conn.close()
    out = {}
    for r in rows:
        s = out.setdefault(r["shelf_id"], {"rows": set(), "cells": set()})
        if r["posicao_coluna"] is None:
            s["rows"].add(r["posicao_linha"])
        else:
            s["cells"].add((r["posicao_linha"], r["posicao_coluna"]))
    return out


def set_disabled_slot(shelf_id: int, row: int, col: int | None) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO disabled_slots (shelf_id, posicao_linha, posicao_coluna) VALUES (?, ?, ?)",
        (shelf_id, row, col))
    conn.commit()
    conn.close()


def unset_disabled_slot(shelf_id: int, row: int, col: int | None) -> None:
    conn = get_connection()
    conn.execute(
        "DELETE FROM disabled_slots WHERE shelf_id=? AND posicao_linha=? AND "
        "(posicao_coluna IS ? OR posicao_coluna=?)",
        (shelf_id, row, col, col))
    conn.commit()
    conn.close()


def clear_disabled_slots(shelf_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM disabled_slots WHERE shelf_id=?", (shelf_id,))
    conn.commit()
    conn.close()


def prune_disabled_slots(shelf_id: int, linhas: int, colunas: int) -> None:
    """Remove bloqueios que caíram fora das dimensões atuais da shelf."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM disabled_slots WHERE shelf_id=? AND "
        "((posicao_coluna IS NULL AND posicao_linha >= ?) OR "
        "(posicao_coluna IS NOT NULL AND (posicao_linha >= ? OR posicao_coluna >= ?)))",
        (shelf_id, linhas, linhas, colunas))
    conn.commit()
    conn.close()
```

`update_shelf` chama `prune_disabled_slots(shelf.id, shelf.linhas, shelf.colunas)` após o UPDATE.

## Organizer integration (`organizers.py`)

Nova helper:

```python
def _is_blocked(shelf_id, row, col, disabled) -> bool:
    if not disabled:
        return False
    d = disabled.get(shelf_id)
    if not d:
        return False
    return row in d["rows"] or (row, col) in d["cells"]
```

Todas as `organize_*` ganham parâmetro opcional `disabled=None`:

```python
def organize_rainbow(cars, shelves, wall=None, disabled=None): ...
def organize_gradient(cars, shelves, wall=None, disabled=None): ...
# (mesma assinatura para todas as 7 funções)
```

`_dispatch_fill` repassa `disabled` para `_fill_grid`/`_fill_wall_grid`.

### `_fill_grid` pula bloqueadas

```python
def _fill_grid(cars, shelves, disabled=None) -> dict:
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
```

### `_fill_wall_grid` idem

Mesmo padrão: `_is_blocked(shelf.id, shelf_row, col, disabled)` antes do assignment.

### `_build_slot_list` filtra ao final

```python
return [s for s in slots if not _is_blocked(s[0], s[1], s[2], disabled)]
```

`_gradient_2d_fill` herda filtro automaticamente (consome `_build_slot_list`).

### `total_slots` subtrai bloqueadas

```python
def total_slots(shelves, disabled=None) -> int:
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
```

Row bloqueada toma precedência: o `continue` impede contagem dupla de células na mesma linha.

## UI — aba Expositores (`app.py`)

Dentro do `st.expander` existente de cada shelf, abaixo do form, nova seção "Vagas bloqueadas". Fora do `st.form` para evitar conflito com widgets existentes:

```python
disabled = get_disabled_slots(shelf.id)
st.markdown("**Vagas bloqueadas**")

row_options = list(range(shelf.linhas))
selected_rows = st.multiselect(
    "Linhas bloqueadas (inteiras)",
    options=row_options,
    default=sorted(disabled["rows"]),
    format_func=lambda r: f"Linha {r+1}",
    key=f"block_rows_{shelf.id}",
)

cell_options = [(r, c) for r in range(shelf.linhas) for c in range(shelf.colunas)]
selected_cells = st.multiselect(
    "Células individuais",
    options=cell_options,
    default=[rc for rc in sorted(disabled["cells"]) if rc[0] not in disabled["rows"]],
    format_func=lambda rc: f"(L{rc[0]+1}, C{rc[1]+1})",
    key=f"block_cells_{shelf.id}",
)

if st.button("Salvar bloqueio", key=f"save_block_{shelf.id}"):
    clear_disabled_slots(shelf.id)
    for r in selected_rows:
        set_disabled_slot(shelf.id, r, None)
    for (r, c) in selected_cells:
        if r not in selected_rows:
            set_disabled_slot(shelf.id, r, c)
    refresh()
    st.rerun()
```

Comportamentos:

- Defaults do multiselect puxam do DB → edição incremental
- `clear_disabled_slots` + inserts = estado consistente após salvar
- Row bloqueada tem precedência: células nela não são inseridas
- Caso de uso principal: selecionar 4 linhas × 2 shelves = 8 cliques + 2 saves

## Visualização (`visualizer.py`)

`render_grid` e helpers ganham `disabled=None`. Plotly shapes não suporta hachura nativa; usa-se cinza sólido `#888888` + texto "✕".

Nova helper aplicada depois de posicionar carros (carros visíveis têm precedência):

```python
def _mark_disabled_for_shelf(disabled, shelf_id, fill_colors, texts, g_row_offset):
    if not disabled:
        return
    d = disabled.get(shelf_id)
    if not d:
        return
    for r in d["rows"]:
        for c in range(len(fill_colors[g_row_offset + r])):
            if texts[g_row_offset + r][c] == "":
                fill_colors[g_row_offset + r][c] = "#888888"
                texts[g_row_offset + r][c] = "✕"
    for (r, c) in d["cells"]:
        if texts[g_row_offset + r][c] == "":
            fill_colors[g_row_offset + r][c] = "#888888"
            texts[g_row_offset + r][c] = "✕"
```

Chamada em `_render_stacked_grid` (com `g_row_offset = sum(s.linhas for s in shelves[:shelf_idx])`) e `_render_wall_grid` (com `g_row_offset = row_offsets[wall_row]`).

Comportamentos visuais:

- Slot bloqueado vazio → cinza `#888888` + "✕"
- Slot bloqueado com carro (caso borda, antes de re-organizar) → carro continua visível
- Demais slots → sem mudança

## Integração no `app.py`

### Carregar disabled no `refresh()`

Adicionar a `refresh()`:

```python
st.session_state.disabled = get_all_disabled_slots()
```

### Tab Organizar (linha ~395)

```python
disabled = st.session_state.disabled
slots = total_slots(shelves, disabled)
if len(cars) > slots:
    st.warning(f"{len(cars)} carros mas apenas {slots} vagas (após bloqueios). Alguns não serão posicionados.")

modo = st.selectbox("Modo de organização", list(ORGANIZERS.keys()))

if st.button("Gerar organização"):
    func = ORGANIZERS[modo]
    assignment = func(cars, shelves, wall, disabled)
    st.session_state.assignment = assignment
    st.rerun()
```

### `render_grid` no preview

```python
fig = render_grid(assignment, cars, shelves, wall, disabled)
```

## Casos borda

1. **Shelf removida** → `ON DELETE CASCADE` limpa `disabled_slots`.
2. **Shelf encolhida** (`update_shelf` com menos linhas/colunas) → `prune_disabled_slots` remove bloqueios fora das novas dimensões.
3. **Carro já posicionado em slot recém-bloqueado** → permanece visível na grade. Próximo "Gerar organização" + "Aplicar" realoca.
4. **Wall grid com múltiplas shelves** → bloqueio é por `shelf_id`, independente da posição na parede.
5. **Sem bloqueios** (`disabled=None`) → caminho atual inalterado, backward compat total.

## Testes (`tests/`)

- `test_disabled_filters_slots_in_fill_grid`: bloqueia 1 linha → `_fill_grid` pula todas as células da linha
- `test_disabled_filters_in_gradient`: bloqueia célula → gradient não posiciona lá
- `test_disabled_filters_in_wall_grid`: bloqueio respeitado no path wall
- `test_total_slots_subtracts_blocked`: 100 total - 40 blocked = 60
- `test_total_slots_no_double_count`: row + cell na mesma linha não duplica
- `test_disabled_crud_roundtrip`: set → get → unset → get vazio
- `test_prune_on_shrink`: shelf 4×10 → 2×10 remove blocked rows 2,3 e cells fora do range
- `test_cascade_on_shelf_delete`: shelf deletada → entries sum
- `test_visualizer_marks_blocked`: cell bloqueada fica cinza + "✕"
- `test_visualizer_keeps_car_in_blocked`: carro em slot bloqueado permanece visível
