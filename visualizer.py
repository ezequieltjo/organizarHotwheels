import plotly.graph_objects as go
from models import Car, ShelfConfig, ParedeConfig

CELL_W = 22
CELL_H = 9


def _mark_disabled_for_shelf(disabled, shelf_id, fill_colors, texts, g_row_offset):
    """Grey out blocked-empty cells. Cars (non-empty text) are NOT overridden."""
    if not disabled:
        return
    d = disabled.get(shelf_id)
    if not d:
        return
    for r in d["rows"]:
        target_row = g_row_offset + r
        if target_row >= len(fill_colors):
            continue
        for c in range(len(fill_colors[target_row])):
            if texts[target_row][c] == "":
                fill_colors[target_row][c] = "#888888"
                texts[target_row][c] = "✕"
    for (r, c) in d["cells"]:
        target_row = g_row_offset + r
        if target_row >= len(fill_colors) or c >= len(fill_colors[target_row]):
            continue
        if texts[target_row][c] == "":
            fill_colors[target_row][c] = "#888888"
            texts[target_row][c] = "✕"


def render_grid(assignment: dict, cars: list[Car], shelves: list[ShelfConfig],
                wall: ParedeConfig = None, disabled: dict = None) -> go.Figure:
    """Render grid visual. assignment: {car_id: (shelf_id, row, col)}"""
    if wall and (wall.linhas > 1 or wall.colunas > 1):
        return _render_wall_grid(assignment, cars, shelves, wall, disabled)
    return _render_stacked_grid(assignment, cars, shelves, disabled)


def _render_stacked_grid(assignment: dict, cars: list[Car], shelves: list[ShelfConfig],
                          disabled: dict = None) -> go.Figure:
    car_map = {c.id: c for c in cars}
    shelf_map = {s.id: s for s in shelves}

    max_col = max((s.colunas for s in shelves), default=0)
    total_rows = sum(s.linhas for s in shelves)

    colors = [["#F0F0F0"] * max_col for _ in range(total_rows)]
    texts = [[""] * max_col for _ in range(total_rows)]
    border_colors = [["#CCCCCC"] * max_col for _ in range(total_rows)]

    row_offset = 0
    for shelf in shelves:
        for s_row in range(shelf.linhas):
            g_row = row_offset + s_row
            for s_col in range(shelf.colunas):
                border_colors[g_row][s_col] = "#999999"
        row_offset += shelf.linhas

    for car_id, (shelf_id, s_row, s_col) in assignment.items():
        car = car_map.get(car_id)
        if not car:
            continue
        shelf = shelf_map.get(shelf_id)
        if not shelf:
            continue
        shelf_idx = shelves.index(shelf)
        g_row = sum(s.linhas for s in shelves[:shelf_idx]) + s_row
        colors[g_row][s_col] = car.cor_hex
        texts[g_row][s_col] = _car_label(car)
        if car.favorito:
            border_colors[g_row][s_col] = "#FFD700"

    # Mark blocked-empty cells grey
    row_offset = 0
    for shelf in shelves:
        _mark_disabled_for_shelf(disabled, shelf.id, colors, texts, row_offset)
        row_offset += shelf.linhas

    fig = go.Figure(data=go.Heatmap(
        z=[[0] * max_col for _ in range(total_rows)],
        colorscale=[[0, "#F0F0F0"], [1, "#F0F0F0"]],
        showscale=False,
        text=texts,
        texttemplate="%{text}",
        textfont={"size": 9},
        hoverongaps=False,
    ))

    shapes = []
    row_offset = 0
    for shelf in shelves:
        # Shelf border (thick)
        shapes.append(dict(
            type="rect",
            x0=-0.5, x1=shelf.colunas - 0.5,
            y0=row_offset - 0.5, y1=row_offset + shelf.linhas - 0.5,
            line=dict(color="#333333", width=4),
            fillcolor="rgba(0,0,0,0)",
        ))
        for r in range(shelf.linhas):
            for c in range(shelf.colunas):
                g_row = row_offset + r
                shapes.append(dict(
                    type="rect",
                    x0=c - 0.5, x1=c + 0.5,
                    y0=g_row - 0.5, y1=g_row + 0.5,
                    line=dict(color=border_colors[g_row][c], width=1),
                    fillcolor=colors[g_row][c],
                ))
        row_offset += shelf.linhas

    total_w = max_col
    total_h = total_rows
    fig.update_layout(
        shapes=shapes,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(range=[-1, total_w + 0.5]),
        margin=dict(l=10, r=10, t=30, b=10),
        height=max(200, total_rows * 25),
    )

    return fig


def _render_wall_grid(assignment: dict, cars: list[Car], shelves: list[ShelfConfig],
                      wall: ParedeConfig, disabled: dict = None) -> go.Figure:
    car_map = {c.id: c for c in cars}
    shelf_map = {s.id: s for s in shelves}

    # Build wall grid
    wall_grid = [[None] * wall.colunas for _ in range(wall.linhas)]
    for shelf in shelves:
        r, c = shelf.parede_linha, shelf.parede_coluna
        if 0 <= r < wall.linhas and 0 <= c < wall.colunas:
            wall_grid[r][c] = shelf

    # Calculate offsets (no gaps between shelves)
    rows_per_wall_row = []
    for wall_row in range(wall.linhas):
        max_r = max((s.linhas for s in wall_grid[wall_row] if s), default=0)
        rows_per_wall_row.append(max_r)

    col_offsets = []
    offset = 0
    for wall_col in range(wall.colunas):
        col_offsets.append(offset)
        max_w = 0
        for wall_row in range(wall.linhas):
            s = wall_grid[wall_row][wall_col]
            if s:
                max_w = max(max_w, s.colunas)
        offset += max_w
    total_cols = offset if offset > 0 else 0

    row_offsets = []
    ro = 0
    for wr in range(wall.linhas):
        row_offsets.append(ro)
        ro += rows_per_wall_row[wr]
    total_rows = ro if ro > 0 else 0

    # Initialize grid
    grid_colors = [["#F0F0F0"] * total_cols for _ in range(total_rows)]
    grid_texts = [[""] * total_cols for _ in range(total_rows)]
    grid_borders = [["#E0E0E0"] * total_cols for _ in range(total_rows)]

    # Draw shelf cells
    for wall_row in range(wall.linhas):
        for wall_col in range(wall.colunas):
            shelf = wall_grid[wall_row][wall_col]
            if not shelf:
                continue
            gr = row_offsets[wall_row]
            gc = col_offsets[wall_col]
            for sr in range(shelf.linhas):
                for sc in range(shelf.colunas):
                    grid_borders[gr + sr][gc + sc] = "#999999"

    # Place cars
    for car_id, (shelf_id, s_row, s_col) in assignment.items():
        car = car_map.get(car_id)
        if not car:
            continue
        shelf = shelf_map.get(shelf_id)
        if not shelf:
            continue
        wall_row, wall_col = shelf.parede_linha, shelf.parede_coluna
        gr = row_offsets[wall_row] + s_row
        gc = col_offsets[wall_col] + s_col
        grid_colors[gr][gc] = car.cor_hex
        grid_texts[gr][gc] = _car_label(car)
        if car.favorito:
            grid_borders[gr][gc] = "#FFD700"

    # Mark blocked-empty cells grey
    for wall_row in range(wall.linhas):
        for wall_col in range(wall.colunas):
            shelf = wall_grid[wall_row][wall_col]
            if not shelf:
                continue
            _mark_disabled_for_shelf(disabled, shelf.id, grid_colors, grid_texts,
                                     row_offsets[wall_row])

    # Build figure
    fig = go.Figure(data=go.Heatmap(
        z=[[0] * total_cols for _ in range(total_rows)],
        colorscale=[[0, "#F0F0F0"], [1, "#F0F0F0"]],
        showscale=False,
        text=grid_texts,
        texttemplate="%{text}",
        textfont={"size": 9},
        hoverongaps=False,
    ))

    shapes = []
    for wall_row in range(wall.linhas):
        for wall_col in range(wall.colunas):
            shelf = wall_grid[wall_row][wall_col]
            if not shelf:
                continue
            gr = row_offsets[wall_row]
            gc = col_offsets[wall_col]

            # Shelf border (thick)
            shapes.append(dict(
                type="rect",
                x0=gc - 0.5, x1=gc + shelf.colunas - 0.5,
                y0=gr - 0.5, y1=gr + shelf.linhas - 0.5,
                line=dict(color="#333333", width=4),
                fillcolor="rgba(0,0,0,0)",
            ))

            for sr in range(shelf.linhas):
                for sc in range(shelf.colunas):
                    cx = gc + sc
                    ry = gr + sr
                    shapes.append(dict(
                        type="rect",
                        x0=cx - 0.5, x1=cx + 0.5,
                        y0=ry - 0.5, y1=ry + 0.5,
                        line=dict(color=grid_borders[ry][cx], width=1),
                        fillcolor=grid_colors[ry][cx],
                    ))

            # Shelf label
            fig.add_annotation(
                x=gc + shelf.colunas / 2 - 0.5,
                y=gr - 0.7,
                text=shelf.nome,
                showarrow=False,
                font=dict(size=10, color="#666666"),
            )

    total_w = total_cols
    total_h = total_rows
    fig.update_layout(
        shapes=shapes,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(range=[-1, total_w + 0.5]),
        margin=dict(l=10, r=10, t=30, b=10),
        height=max(200, total_rows * 25),
    )

    return fig


def _car_label(car: Car) -> str:
    label = car.modelo[:10]
    if car.favorito:
        label = "★ " + label
    return label
