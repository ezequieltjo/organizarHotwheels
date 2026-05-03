import plotly.graph_objects as go
from models import Car, ShelfConfig


def render_grid(assignment: dict, cars: list[Car], shelves: list[ShelfConfig]) -> go.Figure:
    """Render grid visual. assignment: {car_id: (shelf_id, row, col)}"""
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
        for r in range(shelf.linhas):
            for c in range(shelf.colunas):
                g_row = row_offset + r
                shapes.append(dict(
                    type="rect",
                    x0=c - 0.5, x1=c + 0.5,
                    y0=g_row - 0.5, y1=g_row + 0.5,
                    line=dict(color=border_colors[g_row][c], width=2),
                    fillcolor=colors[g_row][c],
                ))
        row_offset += shelf.linhas

    fig.update_layout(
        shapes=shapes,
        yaxis=dict(scaleanchor="x", autorange="reversed"),
        xaxis=dict(constrain="domain"),
        margin=dict(l=10, r=10, t=30, b=10),
        height=max(300, total_rows * 60),
    )

    return fig


def _car_label(car: Car) -> str:
    label = car.modelo[:10]
    if car.favorito:
        label = "★ " + label
    return label
