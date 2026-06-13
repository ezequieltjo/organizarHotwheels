import streamlit as st
from pathlib import Path

st.set_page_config(layout="wide")
from models import Car, ShelfConfig, ParedeConfig
from storage import (init_db, insert_car, get_all_cars, update_car, delete_car,
                     insert_shelf, get_all_shelves, update_shelf, delete_shelf,
                     clear_positions, apply_positions, get_wall_config, save_wall_config,
                     get_all_disabled_slots, get_disabled_slots, set_disabled_slot,
                     clear_disabled_slots)
from importer import import_file
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        organize_favorites_first, total_slots)
from visualizer import render_grid
from color_utils import nome_para_hex
from camera_component import render_color_picker
import time
import base64

PHOTOS_DIR = Path(__file__).parent / "photos"
PHOTOS_DIR.mkdir(exist_ok=True)

ORGANIZERS = {
    "Arco-íris (por cor)": organize_rainbow,
    "Degradê (similaridade)": organize_gradient,
    "Por marca (carro)": organize_by_brand,
    "Por fabricante (miniatura)": organize_by_fabricante,
    "Por ano": organize_by_year,
    "Aleatório": organize_random,
    "Favoritos na frente": organize_favorites_first,
}

init_db()


def refresh():
    st.session_state.cars = get_all_cars()
    st.session_state.shelves = get_all_shelves()
    st.session_state.wall = get_wall_config()
    st.session_state.disabled = get_all_disabled_slots()


if "cars" not in st.session_state:
    refresh()

def _img_b64(path):
    """Read image file, return base64 string."""
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode()


def _save_photo(photo_bytes, modelo):
    """Save photo to disk, return path."""
    ts = int(time.time() * 1000)
    safe = "".join(c if c.isalnum() else "_" for c in modelo)[:30]
    path = str(PHOTOS_DIR / f"{safe}_{ts}.jpg")
    Path(path).write_bytes(photo_bytes)
    return path


# --- Main tabs ---
tab1, tab2, tab3 = st.tabs(["Coleção", "Expositores", "Organizar"])

with tab1:
    st.header(f"Coleção: {len(st.session_state.cars)} carrinhos")

    editing_id = st.session_state.get("editing_car_id")
    editing_car = None
    if editing_id:
        editing_car = next((c for c in st.session_state.cars if c.id == editing_id), None)
        if not editing_car:
            del st.session_state.editing_car_id
            editing_id = None

    c1, c2 = st.columns([3, 2])
    with c2:
        if editing_car:
            st.subheader(f"Editar: {editing_car.modelo}")
            existing_marcas = sorted(set(c.marca for c in st.session_state.cars if c.marca))
            existing_fabricantes = sorted(set(c.fabricante for c in st.session_state.cars if c.fabricante))
            existing_series = sorted(set(c.serie_tipo for c in st.session_state.cars if c.serie_tipo))

            # --- Live color for border preview ---
            _cor_key = f"_cpe_{editing_car.id}"
            live_color = (
                st.session_state.get(_cor_key)
                or editing_car.cor_hex
                or "#808080"
            )

            # --- Photo capture (outside form) ---
            st.markdown("**Foto do carro**")
            if editing_car.foto_path and Path(editing_car.foto_path).exists():
                st.markdown(
                    f"<div style='border:4px solid {live_color};border-radius:8px;overflow:hidden;display:inline-block'>"
                    f"<img src='data:image/jpeg;base64,{_img_b64(editing_car.foto_path)}' style='width:200px;height:auto;display:block'></div>",
                    unsafe_allow_html=True)
            pc1, pc2 = st.columns(2)
            with pc1:
                camera_photo = st.camera_input("📷 Tirar Foto", key="cam_edit")
            with pc2:
                file_photo = st.file_uploader("📁 Upload (substituir)", type=["jpg", "jpeg", "png"], key="upload_edit")

            source = camera_photo or file_photo
            if source:
                st.session_state._pending_photo = source.getvalue()
            elif editing_car.foto_path and Path(editing_car.foto_path).exists():
                st.session_state.setdefault("_pending_photo", Path(editing_car.foto_path).read_bytes())

            # --- Color picker ---
            if st.session_state.get("_pending_photo"):
                st.markdown("**Clique na foto para selecionar a cor**")
                render_color_picker(
                    st.session_state._pending_photo,
                    bridge_key="__bridge_edit__",
                    key="picker_edit",
                    cor_key=_cor_key,
                )

            # --- Form ---
            with st.form("edit_car"):
                modelo = st.text_input("Modelo", value=editing_car.modelo)
                marca_opts = existing_marcas + ["+ Nova marca"]
                marca_idx = marca_opts.index(editing_car.marca) if editing_car.marca in marca_opts else 0
                marca_sel = st.selectbox("Marca do carro", marca_opts, index=marca_idx, key="edit_marca_sel")
                marca_nova = st.text_input("Nova marca (preencher se '+ Nova marca')", key="marca_nova_edit")
                fab_opts = existing_fabricantes + ["+ Novo fabricante"]
                fab_idx = fab_opts.index(editing_car.fabricante) if editing_car.fabricante in fab_opts else 0
                fabricante_sel = st.selectbox("Fabricante da miniatura", fab_opts, index=fab_idx, key="edit_fab_sel")
                fabricante_novo = st.text_input("Novo fabricante (preencher se '+ Novo fabricante')", key="fabricante_novo_edit")
                serie_opts = existing_series + ["+ Nova série"]
                serie_idx = serie_opts.index(editing_car.serie_tipo) if editing_car.serie_tipo in serie_opts else 0
                serie_sel = st.selectbox("Série", serie_opts, index=serie_idx, key="edit_serie_sel")
                serie_nova = st.text_input("Nova série (preencher se '+ Nova série')", key="serie_nova_edit")
                ano = st.number_input("Ano", min_value=1950, max_value=2030, value=editing_car.ano)
                cor = st.text_input("Cor (nome ou #hex)", value=editing_car.cor, placeholder="deixe vazio para usar o seletor")
                default_color = st.session_state.get(_cor_key) or editing_car.cor_hex or "#808080"
                cor_picker = st.color_picker("Seletor de cor", value=default_color, key=_cor_key)
                bc1, bc2 = st.columns(2)
                save = bc1.form_submit_button("Salvar")
                cancel = bc2.form_submit_button("Cancelar")
                if cancel:
                    st.session_state.pop("_pending_photo", None)
                    st.session_state.pop("_pending_picker_color", None)
                    st.session_state.pop("_cpicker_picker_edit", None)
                    del st.session_state.editing_car_id
                    st.rerun()
                if save:
                    marca = marca_nova.strip() if marca_sel == "+ Nova marca" and marca_nova.strip() else (marca_sel if marca_sel != "+ Nova marca" else "")
                    fabricante = fabricante_novo.strip() if fabricante_sel == "+ Novo fabricante" and fabricante_novo.strip() else (fabricante_sel if fabricante_sel != "+ Novo fabricante" else "")
                    serie = serie_nova.strip() if serie_sel == "+ Nova série" and serie_nova.strip() else (serie_sel if serie_sel != "+ Nova série" else "")
                    if modelo.strip():
                        if cor.strip():
                            cor_hex = nome_para_hex(cor.strip())
                        else:
                            cor_hex = cor_picker.upper()
                            cor = ""
                        foto_path = editing_car.foto_path
                        if st.session_state.get("_pending_photo"):
                            foto_path = _save_photo(st.session_state._pending_photo, modelo.strip())
                        editing_car.modelo = modelo.strip()
                        editing_car.marca = marca
                        editing_car.fabricante = fabricante
                        editing_car.ano = ano
                        editing_car.cor = cor.strip()
                        editing_car.cor_hex = cor_hex
                        editing_car.serie_tipo = serie
                        editing_car.foto_path = foto_path
                        update_car(editing_car)
                        st.session_state.pop("_pending_photo", None)
                        st.session_state.pop("_pending_picker_color", None)
                        st.session_state.pop("_cpicker_picker_edit", None)
                        del st.session_state.editing_car_id
                        refresh()
                        st.session_state._car_toast_msg = "Carro editado com sucesso!"
                        st.session_state.car_toast = True
                        st.rerun()
        else:
            st.subheader("Adicionar carro")
            existing_marcas = sorted(set(c.marca for c in st.session_state.cars if c.marca))
            existing_fabricantes = sorted(set(c.fabricante for c in st.session_state.cars if c.fabricante))
            existing_series = sorted(set(c.serie_tipo for c in st.session_state.cars if c.serie_tipo))

            # --- Photo capture (outside form) ---
            st.markdown("**Foto do carro**")
            pc1, pc2 = st.columns(2)
            with pc1:
                camera_photo = st.camera_input("📷 Tirar Foto", key="cam_add")
            with pc2:
                file_photo = st.file_uploader("📁 Upload", type=["jpg", "jpeg", "png"], key="upload_add")

            source = camera_photo or file_photo
            if source:
                st.session_state._pending_photo = source.getvalue()

            # --- Color picker ---
            if st.session_state.get("_pending_photo"):
                st.markdown("**Clique na foto para selecionar a cor**")
                render_color_picker(
                    st.session_state._pending_photo,
                    bridge_key="__bridge_add__",
                    key="picker_add",
                    cor_key="cor_picker_add",
                )
            with st.form("add_car"):
                modelo = st.text_input("Modelo")
                marca_sel = st.selectbox("Marca do carro", existing_marcas + ["+ Nova marca"])
                marca_nova = st.text_input("Nova marca (preencher se '+ Nova marca')", key="marca_nova_add")
                fabricante_sel = st.selectbox("Fabricante da miniatura", existing_fabricantes + ["+ Novo fabricante"])
                fabricante_novo = st.text_input("Novo fabricante (preencher se '+ Novo fabricante')", key="fabricante_novo_add")
                serie_sel = st.selectbox("Série", existing_series + ["+ Nova série"])
                serie_nova = st.text_input("Nova série (preencher se '+ Nova série')", key="serie_nova_add")
                ano = st.number_input("Ano", min_value=1950, max_value=2030, value=2024)
                cor = st.text_input("Cor (nome ou #hex)", placeholder="deixe vazio para usar o seletor")
                default_color = st.session_state.get("cor_picker_add") or "#808080"
                cor_picker = st.color_picker("Seletor de cor", value=default_color, key="cor_picker_add")
                if st.form_submit_button("Adicionar"):
                    marca = marca_nova.strip() if marca_sel == "+ Nova marca" and marca_nova.strip() else (marca_sel if marca_sel != "+ Nova marca" else "")
                    fabricante = fabricante_novo.strip() if fabricante_sel == "+ Novo fabricante" and fabricante_novo.strip() else (fabricante_sel if fabricante_sel != "+ Novo fabricante" else "")
                    serie = serie_nova.strip() if serie_sel == "+ Nova série" and serie_nova.strip() else (serie_sel if serie_sel != "+ Nova série" else "")
                    if modelo.strip():
                        if cor.strip():
                            cor_hex = nome_para_hex(cor.strip())
                        else:
                            cor_hex = cor_picker.upper()
                            cor = ""
                        foto_path = ""
                        if st.session_state.get("_pending_photo"):
                            foto_path = _save_photo(st.session_state._pending_photo, modelo.strip())
                        insert_car(Car(
                            modelo=modelo.strip(), marca=marca,
                            fabricante=fabricante, ano=ano,
                            cor=cor.strip(), cor_hex=cor_hex, serie_tipo=serie,
                            foto_path=foto_path
                        ))
                        st.session_state.pop("_pending_photo", None)
                        st.session_state.pop("_pending_picker_color", None)
                        st.session_state.pop("_cpicker_picker_add", None)
                        st.session_state.pop("cor_picker_add", None)
                        refresh()
                        st.session_state._car_toast_msg = "Carro adicionado com sucesso!"
                        st.session_state.car_toast = True
                        st.rerun()

    with c1:
        busca = st.text_input("Buscar", placeholder="modelo, marca, fabricante ou série...", key="busca_cars")
        cars = st.session_state.cars
        if busca.strip():
            b = busca.lower()
            cars = [c for c in cars if b in c.modelo.lower() or b in c.marca.lower() or b in c.fabricante.lower() or b in c.serie_tipo.lower()]

        filtro_serie = st.selectbox("Filtrar série", ["Todas"] + list(dict.fromkeys(c.serie_tipo for c in st.session_state.cars if c.serie_tipo)), key="filtro_serie")
        if filtro_serie != "Todas":
            cars = [c for c in cars if c.serie_tipo == filtro_serie]

        ordem_opts = [
            "Adição (recentes primeiro)", "Adição (antigos primeiro)",
            "Alfabética (A-Z)", "Alfabética (Z-A)",
            "Ano (crescente)", "Ano (decrescente)",
            "Modificação (recentes primeiro)", "Modificação (antigos primeiro)",
        ]
        ordem = st.selectbox("Ordenar por", ordem_opts, key="ordem_cars")
        match ordem:
            case "Alfabética (A-Z)":
                cars = sorted(cars, key=lambda c: c.modelo.lower())
            case "Alfabética (Z-A)":
                cars = sorted(cars, key=lambda c: c.modelo.lower(), reverse=True)
            case "Ano (crescente)":
                cars = sorted(cars, key=lambda c: c.ano)
            case "Ano (decrescente)":
                cars = sorted(cars, key=lambda c: c.ano, reverse=True)
            case "Adição (recentes primeiro)":
                cars = sorted(cars, key=lambda c: c.created_at or "", reverse=True)
            case "Adição (antigos primeiro)":
                cars = sorted(cars, key=lambda c: c.created_at or "")
            case "Modificação (recentes primeiro)":
                cars = sorted(cars, key=lambda c: c.updated_at or "", reverse=True)
            case "Modificação (antigos primeiro)":
                cars = sorted(cars, key=lambda c: c.updated_at or "")

        for car in cars:
            with st.container():
                col1, col2, col3 = st.columns([1, 6, 2])
                with col1:
                    if car.foto_path and Path(car.foto_path).exists():
                        st.markdown(
                            f"<div style='border:3px solid {car.cor_hex};border-radius:6px;overflow:hidden;width:60px;height:45px'>"
                            f"<img src='data:image/jpeg;base64,{_img_b64(car.foto_path)}' style='width:100%;height:100%;object-fit:cover'></div>",
                            unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='width:60px;height:45px;background:{car.cor_hex};border-radius:4px'></div>",
                                    unsafe_allow_html=True)
                with col2:
                    fav = "★ " if car.favorito else ""
                    st.write(f"**{car.marca} {fav}{car.modelo}** — {car.fabricante or '?'} | {car.serie_tipo}")
                with col3:
                    bc1, bc2, bc3 = st.columns(3)
                    if bc1.button("⭐", key=f"fav_{car.id}"):
                        car.favorito = not car.favorito
                        update_car(car)
                        refresh()
                        st.rerun()
                    if bc2.button("✏️", key=f"edit_{car.id}"):
                        st.session_state.editing_car_id = car.id
                        st.session_state.pop("_pending_photo", None)
                        st.session_state.pop("_pending_picker_color", None)
                        st.session_state.pop("_cpicker_picker_edit", None)
                        st.rerun()
                    if bc3.button("🗑️", key=f"del_{car.id}"):
                        st.session_state.pop("_pending_photo", None)
                        st.session_state.pop("_pending_picker_color", None)
                        delete_car(car.id)
                        refresh()
                        st.session_state._car_toast_msg = "Carro removido!"
                        st.session_state.car_toast = "delete"
                        st.rerun()

with tab2:
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

                row_options = list(range(shelf.linhas))
                selected_rows = st.multiselect(
                    "Linhas bloqueadas (inteiras)",
                    options=row_options,
                    default=sorted(current["rows"]),
                    format_func=lambda r: f"Linha {r+1}",
                    key=f"block_rows_{shelf.id}",
                )

                cell_options = [(r, c) for r in range(shelf.linhas)
                                for c in range(shelf.colunas)]
                selected_cells = st.multiselect(
                    "Células individuais",
                    options=cell_options,
                    default=[rc for rc in sorted(current["cells"])
                             if rc[0] not in current["rows"]],
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

    with ec2:
        shelves = st.session_state.shelves
        cars = st.session_state.cars
        if shelves:
            positioned = [c for c in cars if c.expositor_id is not None]
            if positioned:
                assignment = {c.id: (c.expositor_id, c.posicao_linha, c.posicao_coluna)
                              for c in positioned}
                fig = render_grid(assignment, cars, shelves, wall, st.session_state.disabled)
                st.plotly_chart(fig, use_container_width=True, key="grid_expositores")
            else:
                st.info("Nenhum carro posicionado ainda. Use a aba Organizar.")

with tab3:
    st.header("Organizar")
    cars = st.session_state.cars
    shelves = st.session_state.shelves
    wall = st.session_state.wall

    if not shelves:
        st.warning("Adicione pelo menos um expositor na aba Expositores.")
    elif not cars:
        st.warning("Adicione carros à coleção primeiro.")
    else:
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

        if "assignment" in st.session_state and st.session_state.assignment:
            assignment = st.session_state.assignment
            fig = render_grid(assignment, cars, shelves, wall, disabled)
            st.plotly_chart(fig, use_container_width=True, key="grid_organizar")

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

    st.divider()
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

# Single script at end: button styling + toast
_toast_type = st.session_state.pop("car_toast", None)
_toast_msg = st.session_state.pop("_car_toast_msg", "").replace("'", "&#39;")

_toast_icon = "🗑️" if _toast_type == "delete" else "✅"
_toast_bg = "#c62828" if _toast_type == "delete" else "#2e7d32"
_toast_js = ""
if _toast_type:
    _toast_js = (
        f'var t=d.createElement("div");'
        f't.textContent="{_toast_icon} {_toast_msg}";'
        f't.style.cssText="position:fixed;bottom:20px;left:50%;transform:translateX(-50%);'
        f'background:{_toast_bg};color:#fff;padding:10px 24px;border-radius:8px;'
        f'font-size:1rem;z-index:99999;font-family:sans-serif;transition:opacity 0.3s;";'
        f'd.body.appendChild(t);'
        f'setTimeout(function(){{t.style.opacity="0";}},500);'
        f'setTimeout(function(){{t.remove();}},800);'
    )

st.html(f"""<script>
(function(){{
  var d=parent.document;
  var s=d.createElement('style');
  s.textContent=`
    .car-action-col{{display:flex!important;justify-content:center!important;}}
    .car-action-col button{{display:flex!important;justify-content:center!important;align-items:center!important;font-size:1.3rem!important;padding:0!important;width:38px!important;height:38px!important;min-width:38px!important;max-width:38px!important;border-radius:8px!important;margin:0 auto!important;line-height:1!important;}}
  `;
  d.head.appendChild(s);
  function markButtons(){{
    d.querySelectorAll('button').forEach(function(b){{
      var t=b.textContent.trim();
      if((t==='⭐'||t==='✏️'||t==='🗑️')&&b.closest('[data-testid="stColumn"]')){{
        b.closest('[data-testid="stColumn"]').classList.add('car-action-col');
      }}
    }});
  }}
  markButtons();
  setInterval(markButtons,300);
  {_toast_js}
}})();
</script>""", unsafe_allow_javascript=True)
