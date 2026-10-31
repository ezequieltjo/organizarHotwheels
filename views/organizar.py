"""Aba Organizar: importar planilha, gerar e aplicar organização."""
import streamlit as st

from importer import import_file
from models import GradientConfig
from storage import clear_positions, apply_positions, insert_car
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        total_slots)
from ui.photos import PHOTOS_DIR
from ui.state import refresh
from visualizer import render_grid

# favoritos dormente: organize_favorites_first segue em organizers.py, fora da lista
ORGANIZERS = {
    "Arco-íris (por cor)": organize_rainbow,
    "Degradê (moldura)": organize_gradient,
    "Por marca (carro)": organize_by_brand,
    "Por fabricante (miniatura)": organize_by_fabricante,
    "Por ano": organize_by_year,
    "Aleatório": organize_random,
}


def render() -> None:
    st.header("Organizar")
    cars = [c for c in st.session_state.cars if not c.lista_desejos]
    shelves = st.session_state.shelves
    wall = st.session_state.wall

    # Resultado: organização gerada ou posições salvas (fallback)
    assignment = st.session_state.get("assignment")
    if not assignment:
        positioned = [c for c in cars if c.expositor_id is not None]
        if positioned:
            assignment = {c.id: (c.expositor_id, c.posicao_linha, c.posicao_coluna)
                          for c in positioned}

    org_l, org_r, org_p = st.columns([1, 2, 1.5], gap="large")

    with org_l:
        # --- Importar CSV/Excel (topo da coluna de configuração) ---
        st.subheader("Importar CSV/Excel")
        uploaded = st.file_uploader("Arquivo", type=["csv", "xlsx", "xls"], key="import_file")
        if uploaded and st.button("Importar"):
            tmp = PHOTOS_DIR / uploaded.name
            tmp.write_bytes(uploaded.getbuffer())
            cars_imported = import_file(tmp)
            for car in cars_imported:
                insert_car(car)
            tmp.unlink()
            refresh()
            st.success(f"{len(cars_imported)} carros importados!")
            st.rerun()

        # --- Configuração do modo ---
        if not shelves:
            st.warning("Adicione pelo menos um expositor na aba Expositores.")
        elif not cars:
            st.warning("Adicione carros à coleção primeiro.")
        else:
            disabled = st.session_state.disabled
            active_cars = [c for c in cars if not c.reserva]
            slots = total_slots(shelves, disabled)
            if len(active_cars) > slots:
                n_reservas = len(cars) - len(active_cars)
                reserva_note = f" ({n_reservas} arquivados)" if n_reservas > 0 else ""
                st.warning(f"{len(active_cars)} carros ativos mas apenas {slots} vagas{reserva_note}. "
                           f"Alguns não serão posicionados.")

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

    with org_r:
        # --- Expositor com o resultado ---
        if shelves and cars and assignment:
            disabled = st.session_state.disabled
            fig = render_grid(assignment, cars, shelves, wall, disabled)
            # grid centralizado; quando mais largo que a coluna, rola horizontal
            st.markdown(
                "<style>"
                "div[data-testid='stElementContainer']:has([data-testid=stPlotlyChart])"
                "{display:flex !important;overflow-x:auto !important;}"
                "div[data-testid='stPlotlyChart']"
                "{width:fit-content !important;margin:0 auto !important;flex:none !important;}"
                "</style>",
                unsafe_allow_html=True)
            st.plotly_chart(fig, width=int(fig.layout.width), key="grid_organizar")

    with org_p:
        # --- Posições (terceira coluna) ---
        if shelves and cars and assignment:
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
