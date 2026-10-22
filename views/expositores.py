"""Aba Expositores: configuração da parede, expositores e vagas bloqueadas."""
import streamlit as st

from models import ShelfConfig
from storage import (insert_shelf, update_shelf, delete_shelf, replace_disabled_slots,
                     get_wall_config, save_wall_config, get_disabled_slots)
from ui.state import refresh
from visualizer import render_grid


def render() -> None:
    st.header("Expositores")
    wall = st.session_state.wall

    ec1, ec2 = st.columns([1, 2])
    with ec1:
        st.subheader("Parede")
        w_linhas = st.number_input("Linhas de expositores", min_value=1, max_value=10,
                                   value=wall.linhas, key="wall_linhas")
        w_colunas = st.number_input("Colunas de expositores", min_value=1, max_value=10,
                                    value=wall.colunas, key="wall_colunas")
        if st.button("Salvar parede"):
            save_wall_config(w_linhas, w_colunas)
            refresh()
            st.rerun()

        st.subheader("Adicionar expositor")
        with st.form("add_shelf"):
            nome = st.text_input("Nome")
            linhas = st.number_input("Linhas", min_value=1, max_value=20, value=4, key="shelf_linhas")
            colunas = st.number_input("Colunas", min_value=1, max_value=30, value=10, key="shelf_colunas")
            if st.form_submit_button("Adicionar"):
                if nome.strip():
                    insert_shelf(ShelfConfig(nome=nome.strip(), linhas=linhas, colunas=colunas))
                    refresh()
                    st.rerun()

        wall = st.session_state.wall
        for shelf in st.session_state.shelves:
            with st.expander(f"{shelf.nome} ({shelf.linhas}x{shelf.colunas})"):
                with st.form(f"shelf_form_{shelf.id}"):
                    new_nome = st.text_input("Nome", value=shelf.nome)
                    new_lin = st.number_input("Linhas", value=shelf.linhas, min_value=1, max_value=20)
                    new_col = st.number_input("Colunas", value=shelf.colunas, min_value=1, max_value=30)
                    p_linha = st.selectbox("Linha na parede", range(wall.linhas),
                                           index=min(shelf.parede_linha, wall.linhas - 1))
                    p_coluna = st.selectbox("Coluna na parede", range(wall.colunas),
                                            index=min(shelf.parede_coluna, wall.colunas - 1))
                    bc1, bc2 = st.columns(2)
                    save_btn = bc1.form_submit_button("Salvar")
                    del_btn = bc2.form_submit_button("Remover")
                    if save_btn:
                        shelf.nome = new_nome.strip()
                        shelf.linhas = new_lin
                        shelf.colunas = new_col
                        shelf.parede_linha = p_linha
                        shelf.parede_coluna = p_coluna
                        update_shelf(shelf)
                        refresh()
                        st.rerun()
                    if del_btn:
                        delete_shelf(shelf.id)
                        refresh()
                        st.rerun()

                # Vagas bloqueadas
                current = get_disabled_slots(shelf.id)
                st.markdown("**Vagas bloqueadas**")

                with st.form(f"block_form_{shelf.id}"):
                    row_options = list(range(shelf.linhas))
                    selected_rows = st.multiselect(
                        "Linhas bloqueadas (inteiras)",
                        options=row_options,
                        default=sorted(current["rows"]),
                        format_func=lambda r: f"Linha {r+1}",
                        key=f"block_rows_{shelf.id}",
                    )

                    cell_options = [(r, c) for r in range(shelf.linhas) if r not in selected_rows
                                    for c in range(shelf.colunas)]
                    selected_cells = st.multiselect(
                        "Células individuais",
                        options=cell_options,
                        default=[rc for rc in sorted(current["cells"])
                                 if rc[0] not in current["rows"]],
                        format_func=lambda rc: f"(L{rc[0]+1}, C{rc[1]+1})",
                        key=f"block_cells_{shelf.id}",
                    )

                    if st.form_submit_button("Salvar bloqueio"):
                        cells_to_set = [(r, c) for (r, c) in selected_cells if r not in selected_rows]
                        replace_disabled_slots(shelf.id, selected_rows, cells_to_set)
                        refresh()
                        st.rerun()

    with ec2:
        shelves = st.session_state.shelves
        cars = st.session_state.cars
        if shelves:
            positioned = [c for c in cars if c.expositor_id is not None]
            if positioned:
                assignment = {c.id: (c.expositor_id, c.posicao_linha, c.posicao_coluna)
                              for c in positioned}
                fig = render_grid(assignment, cars, shelves, wall, st.session_state.disabled)
                st.plotly_chart(fig, width=int(fig.layout.width), key="grid_expositores")
            else:
                st.info("Nenhum carro posicionado ainda. Use a aba Organizar.")
