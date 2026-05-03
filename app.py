import streamlit as st
from pathlib import Path
from models import Car, ShelfConfig
from storage import (init_db, insert_car, get_all_cars, update_car, delete_car,
                     insert_shelf, get_all_shelves, update_shelf, delete_shelf,
                     clear_positions, apply_positions)
from importer import import_file
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_year, organize_random, organize_favorites_first,
                        total_slots)
from visualizer import render_grid
from color_utils import nome_para_hex

PHOTOS_DIR = Path(__file__).parent / "photos"
PHOTOS_DIR.mkdir(exist_ok=True)

ORGANIZERS = {
    "Arco-íris (por cor)": organize_rainbow,
    "Degradê (similaridade)": organize_gradient,
    "Por marca": organize_by_brand,
    "Por ano": organize_by_year,
    "Aleatório": organize_random,
    "Favoritos na frente": organize_favorites_first,
}

init_db()


def refresh():
    st.session_state.cars = get_all_cars()
    st.session_state.shelves = get_all_shelves()


if "cars" not in st.session_state:
    refresh()

# --- Sidebar ---
with st.sidebar:
    st.header("Expositores")
    with st.expander("Adicionar expositor"):
        nome = st.text_input("Nome", key="shelf_nome")
        linhas = st.number_input("Linhas", min_value=1, max_value=20, value=4, key="shelf_linhas")
        colunas = st.number_input("Colunas", min_value=1, max_value=30, value=10, key="shelf_colunas")
        if st.button("Adicionar"):
            if nome.strip():
                insert_shelf(ShelfConfig(nome=nome.strip(), linhas=linhas, colunas=colunas))
                refresh()
                st.rerun()

    for shelf in st.session_state.shelves:
        with st.expander(f"{shelf.nome} ({shelf.linhas}x{shelf.colunas})"):
            new_nome = st.text_input("Nome", value=shelf.nome, key=f"sn_{shelf.id}")
            new_lin = st.number_input("Linhas", value=shelf.linhas, min_value=1, max_value=20, key=f"sl_{shelf.id}")
            new_col = st.number_input("Colunas", value=shelf.colunas, min_value=1, max_value=30, key=f"sc_{shelf.id}")
            c1, c2 = st.columns(2)
            if c1.button("Salvar", key=f"ss_{shelf.id}"):
                shelf.nome = new_nome.strip()
                shelf.linhas = new_lin
                shelf.colunas = new_col
                update_shelf(shelf)
                refresh()
                st.rerun()
            if c2.button("Remover", key=f"sd_{shelf.id}"):
                delete_shelf(shelf.id)
                refresh()
                st.rerun()

    st.divider()
    st.header("Importar CSV/Excel")
    uploaded = st.file_uploader("Arquivo", type=["csv", "xlsx", "xls"], key="import_file")
    if uploaded and st.button("Importar"):
        tmp = PHOTOS_DIR / uploaded.name
        tmp.write_bytes(uploaded.getbuffer())
        cars = import_file(tmp)
        for car in cars:
            insert_car(car)
        tmp.unlink()
        refresh()
        st.success(f"{len(cars)} carros importados!")
        st.rerun()

# --- Main tabs ---
tab1, tab2, tab3 = st.tabs(["Coleção", "Organizar", "Expositores"])

with tab1:
    st.header("Coleção")

    c1, c2 = st.columns([3, 1])
    with c2:
        st.subheader("Adicionar carro")
        with st.form("add_car"):
            modelo = st.text_input("Modelo")
            marca = st.text_input("Marca")
            ano = st.number_input("Ano", min_value=1950, max_value=2030, value=2024)
            cor = st.text_input("Cor (nome ou #hex)")
            serie = st.selectbox("Série", ["Mainline", "Premium", "Treasure Hunt", "Super Treasure Hunt", "Outra"])
            foto = st.file_uploader("Foto", type=["jpg", "jpeg", "png"], key="car_foto")
            if st.form_submit_button("Adicionar"):
                if modelo.strip():
                    cor_hex = nome_para_hex(cor.strip()) if cor.strip() else "#808080"
                    foto_path = ""
                    if foto:
                        ext = Path(foto.name).suffix
                        foto_path = str(PHOTOS_DIR / f"{modelo.strip()}{ext}")
                        Path(foto_path).write_bytes(foto.getbuffer())
                    insert_car(Car(
                        modelo=modelo.strip(), marca=marca.strip(), ano=ano,
                        cor=cor.strip(), cor_hex=cor_hex, serie_tipo=serie,
                        foto_path=foto_path
                    ))
                    refresh()
                    st.rerun()

    with c1:
        busca = st.text_input("Buscar", placeholder="modelo, marca ou série...")
        cars = st.session_state.cars
        if busca.strip():
            b = busca.lower()
            cars = [c for c in cars if b in c.modelo.lower() or b in c.marca.lower() or b in c.serie_tipo.lower()]

        filtro_serie = st.selectbox("Filtrar série", ["Todas"] + list(dict.fromkeys(c.serie_tipo for c in st.session_state.cars if c.serie_tipo)))
        if filtro_serie != "Todas":
            cars = [c for c in cars if c.serie_tipo == filtro_serie]

        for car in cars:
            with st.container():
                col1, col2, col3 = st.columns([1, 4, 1])
                with col1:
                    if car.foto_path and Path(car.foto_path).exists():
                        st.image(car.foto_path, width=60)
                    else:
                        st.markdown(f"<div style='width:60px;height:45px;background:{car.cor_hex};border-radius:4px'></div>",
                                    unsafe_allow_html=True)
                with col2:
                    fav = "★ " if car.favorito else ""
                    st.write(f"**{fav}{car.modelo}** — {car.marca} ({car.ano}) | {car.cor} | {car.serie_tipo}")
                with col3:
                    if st.button("★", key=f"fav_{car.id}"):
                        car.favorito = not car.favorito
                        update_car(car)
                        refresh()
                        st.rerun()
                    if st.button("🗑", key=f"del_{car.id}"):
                        delete_car(car.id)
                        refresh()
                        st.rerun()

with tab2:
    st.header("Organizar")
    cars = st.session_state.cars
    shelves = st.session_state.shelves

    if not shelves:
        st.warning("Adicione pelo menos um expositor na sidebar.")
    elif not cars:
        st.warning("Adicione carros à coleção primeiro.")
    else:
        slots = total_slots(shelves)
        if len(cars) > slots:
            st.warning(f"{len(cars)} carros mas apenas {slots} vagas. Alguns não serão posicionados.")

        modo = st.selectbox("Modo de organização", list(ORGANIZERS.keys()))

        if st.button("Gerar organização"):
            func = ORGANIZERS[modo]
            assignment = func(cars, shelves)
            st.session_state.assignment = assignment
            st.rerun()

        if "assignment" in st.session_state and st.session_state.assignment:
            assignment = st.session_state.assignment
            fig = render_grid(assignment, cars, shelves)
            st.plotly_chart(fig, use_container_width=True)

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
            st.dataframe(pos_data, use_container_width=True, hide_index=True)

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

with tab3:
    st.header("Expositores")
    shelves = st.session_state.shelves
    cars = st.session_state.cars

    if not shelves:
        st.info("Nenhum expositor cadastrado.")
    else:
        positioned = [c for c in cars if c.expositor_id is not None]
        if not positioned:
            st.info("Nenhum carro posicionado. Use a aba Organizar.")
        else:
            assignment = {c.id: (c.expositor_id, c.posicao_linha, c.posicao_coluna)
                          for c in positioned}
            fig = render_grid(assignment, cars, shelves)
            st.plotly_chart(fig, use_container_width=True)

            for shelf in shelves:
                shelf_cars = [c for c in positioned if c.expositor_id == shelf.id]
                if shelf_cars:
                    st.subheader(shelf.nome)
                    for car in sorted(shelf_cars, key=lambda c: (c.posicao_linha, c.posicao_coluna)):
                        pos = f"L{car.posicao_linha + 1} C{car.posicao_coluna + 1}"
                        fav = "★ " if car.favorito else ""
                        st.write(f"- {pos}: {fav}{car.modelo} ({car.cor})")
