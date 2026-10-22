"""Aba Coleção: lista de carros, formulários de adicionar e editar."""
from datetime import date

import streamlit as st

import base64

from models import Car
from storage import insert_car, update_car, delete_car, set_reserva
from camera_component import render_color_picker
from color_sliders import render_color_sliders
from ui.state import refresh
from ui.photos import resolve_photo, save_photo
from ui.cards import render_car_list


def act_favorito(car) -> None:
    car.favorito = not car.favorito
    update_car(car)
    refresh()
    st.rerun()


def act_reserva(car) -> None:
    set_reserva(car.id, not car.reserva)
    refresh()
    st.rerun()


def act_editar(car) -> None:
    st.session_state.editing_car_id = car.id
    st.session_state.pop("_pending_photo", None)
    st.session_state.pop("_pending_picker_color", None)
    st.session_state.pop("_cpicker_picker_edit", None)
    st.rerun()


def act_excluir(car) -> None:
    st.session_state.pop("_pending_photo", None)
    st.session_state.pop("_pending_picker_color", None)
    delete_car(car.id)
    refresh()
    st.session_state._car_toast_msg = "Carro removido!"
    st.session_state.car_toast = "delete"
    st.rerun()


def act_promover(car) -> None:
    """Lista de desejos -> coleção."""
    car.lista_desejos = False
    update_car(car)
    refresh()
    st.session_state._car_toast_msg = "Adicionado à coleção!"
    st.session_state.car_toast = True
    st.rerun()


COLECAO_ACTIONS = [
    (lambda c: ":material/star:" if c.favorito else ":material/star_border:",
     "Favoritar/desfavoritar", act_favorito),
    (lambda c: ":material/inventory_2:" if c.reserva else ":material/inventory:",
     "Arquivar/desarquivar (não posiciona)", act_reserva),
    (lambda c: ":material/edit:", "Editar", act_editar),
    (lambda c: ":material/delete:", "Excluir", act_excluir),
]


def render() -> None:
    colecao = [c for c in st.session_state.cars if not c.lista_desejos]
    n_reservas = sum(1 for c in colecao if c.reserva)
    # repetidos = unidades extras; a primeira de cada (modelo, marca) não conta
    n_repetidos = len(colecao) - len({(c.modelo, c.marca) for c in colecao})
    detalhes = ", ".join(f"{n} {lbl}" for n, lbl in
                         ((n_repetidos, "repetidos"), (n_reservas, "arquivados")) if n)
    st.header(f"Coleção: {len(colecao)} carrinhos"
              + (f" ({detalhes})" if detalhes else ""))

    editing_id = st.session_state.get("editing_car_id")
    editing_car = None
    if editing_id:
        editing_car = next((c for c in st.session_state.cars if c.id == editing_id), None)
        if not editing_car:
            del st.session_state.editing_car_id
            editing_id = None

    c1, c2 = st.columns([3, 2])
    # Lista (c1) ANTES do form (c2): o submit do form aborta a run via st.rerun();
    # se a toolbar de filtros ainda não registrou os widgets, Streamlit descarta
    # os valores e os filtros resetam. Renderizando c1 primeiro, os widgets já
    # existem quando o abort acontece e os filtros persistem.
    with c1:
        render_car_list(colecao, "cars", COLECAO_ACTIONS)
    with c2:
        if editing_car:
            _render_editar(editing_car)
        else:
            _render_adicionar()


def _render_editar(editing_car) -> None:
    st.subheader(f"Editar: {editing_car.modelo}")
    existing_marcas = sorted(set(c.marca for c in st.session_state.cars if c.marca))
    existing_fabricantes = sorted(set(c.fabricante for c in st.session_state.cars if c.fabricante))
    existing_series = sorted(set(c.serie_tipo for c in st.session_state.cars if c.serie_tipo))

    # --- Live color for border preview ---
    _cor_key = f"_cpe_{editing_car.id}"
    # Seed ANTES do color_picker: sem isso o widget nasce preto (#000000)
    # e sobrescreve a cor salva no save.
    if _cor_key not in st.session_state:
        st.session_state[_cor_key] = (editing_car.cor_hex or "#808080").upper()
    live_color = (
        st.session_state.get(_cor_key)
        or editing_car.cor_hex
        or "#808080"
    )

    # --- Foto: upload + swatches à esquerda, preview à direita ---
    with st.container(border=True):
        st.markdown("**Imagem da Miniatura**")
        pc1, pc2 = st.columns(2)
        with pc1:
            file_photo = st.file_uploader("📁 Upload (substituir)", type=["jpg", "jpeg", "png", "webp"], key="upload_edit")
            if file_photo:
                st.session_state._pending_photo = file_photo.getvalue()
            elif (_existing := resolve_photo(editing_car.foto_path)) is not None:
                st.session_state.setdefault("_pending_photo", _existing.read_bytes())
            if st.session_state.get("_pending_photo"):
                render_color_picker(
                    st.session_state._pending_photo,
                    bridge_key="__bridge_edit__",
                    key="picker_edit",
                    cor_key=_cor_key,
                )
        with pc2:
            if st.session_state.get("_pending_photo"):
                _b64 = base64.b64encode(st.session_state._pending_photo).decode()
                st.markdown(
                    f"<div style='border:4px solid {live_color};border-radius:8px;overflow:hidden'>"
                    f"<img src='data:image/jpeg;base64,{_b64}' style='width:100%;height:320px;object-fit:cover;display:block'></div>",
                    unsafe_allow_html=True)

    # --- Form ---
    with st.form("edit_car"):
        l1c1, l1c2 = st.columns(2)
        with l1c1:
            marca_opts = existing_marcas + ["+ Nova marca"]
            marca_idx = marca_opts.index(editing_car.marca) if editing_car.marca in marca_opts else 0
            marca_sel = st.selectbox("Marca do carro", marca_opts, index=marca_idx, key="edit_marca_sel")
        with l1c2:
            modelo = st.text_input("Modelo", value=editing_car.modelo)
        l2c1, l2c2 = st.columns(2)
        with l2c1:
            fab_opts = existing_fabricantes + ["+ Novo fabricante"]
            fab_idx = fab_opts.index(editing_car.fabricante) if editing_car.fabricante in fab_opts else 0
            fabricante_sel = st.selectbox("Fabricante da miniatura", fab_opts, index=fab_idx, key="edit_fab_sel")
        with l2c2:
            serie_opts = existing_series + ["+ Nova série"]
            serie_idx = serie_opts.index(editing_car.serie_tipo) if editing_car.serie_tipo in serie_opts else 0
            serie_sel = st.selectbox("Série", serie_opts, index=serie_idx, key="edit_serie_sel")
        l3c1, l3c2 = st.columns(2)
        with l3c1:
            ano = st.number_input("Ano", min_value=1950, max_value=2030, value=editing_car.ano)
        with l3c2:
            data_inicial = (date.fromisoformat(editing_car.created_at[:10])
                            if editing_car.created_at else date.today())
            data_adicao = st.date_input("Data de adição à coleção", value=data_inicial,
                                        format="DD/MM/YYYY")
        fc1, fc2, _ = st.columns(3)
        with fc1:
            reserva_edit = st.checkbox("Arquivado (não posicionar em expositor)", value=editing_car.reserva)
        with fc2:
            customizada_edit = st.checkbox("Customização", value=editing_car.customizada)
        _, btn_col, _ = st.columns([1, 1, 1])
        with btn_col:
            sb1, sb2 = st.columns(2)
            save = sb1.form_submit_button("Salvar", type="primary", use_container_width=True)
            cancel = sb2.form_submit_button("Cancelar", use_container_width=True)
        if cancel:
            st.session_state.pop("_pending_photo", None)
            st.session_state.pop("_pending_picker_color", None)
            st.session_state.pop("_cpicker_picker_edit", None)
            del st.session_state.editing_car_id
            st.rerun()
        if save:
            marca_nova = st.session_state.get("marca_nova_edit", "")
            fabricante_novo = st.session_state.get("fabricante_novo_edit", "")
            serie_nova = st.session_state.get("serie_nova_edit", "")
            marca = marca_nova.strip() if marca_sel == "+ Nova marca" and marca_nova.strip() else (marca_sel if marca_sel != "+ Nova marca" else "")
            fabricante = fabricante_novo.strip() if fabricante_sel == "+ Novo fabricante" and fabricante_novo.strip() else (fabricante_sel if fabricante_sel != "+ Novo fabricante" else "")
            serie = serie_nova.strip() if serie_sel == "+ Nova série" and serie_nova.strip() else (serie_sel if serie_sel != "+ Nova série" else "")
            if modelo.strip():
                cor_hex = (st.session_state.get(_cor_key) or editing_car.cor_hex or "#808080").upper()
                cor = ""
                foto_path = editing_car.foto_path
                if st.session_state.get("_pending_photo"):
                    foto_path = save_photo(
                        st.session_state._pending_photo,
                        modelo.strip(),
                        old_path=editing_car.foto_path,
                    )
                editing_car.modelo = modelo.strip()
                editing_car.marca = marca
                editing_car.fabricante = fabricante
                editing_car.ano = ano
                editing_car.cor = cor.strip()
                editing_car.cor_hex = cor_hex
                editing_car.serie_tipo = serie
                editing_car.foto_path = foto_path
                editing_car.reserva = reserva_edit
                editing_car.customizada = customizada_edit
                hora = editing_car.created_at[11:] if editing_car.created_at else "00:00:00"
                editing_car.created_at = f"{data_adicao.isoformat()} {hora}"
                if reserva_edit and editing_car.expositor_id is not None:
                    update_car(editing_car, created_at=editing_car.created_at)
                    set_reserva(editing_car.id, True)  # atomic clear of position
                else:
                    update_car(editing_car, created_at=editing_car.created_at)
                st.session_state.pop("_pending_photo", None)
                st.session_state.pop("_pending_picker_color", None)
                st.session_state.pop("_cpicker_picker_edit", None)
                del st.session_state.editing_car_id
                refresh()
                st.session_state._car_toast_msg = "Carro editado com sucesso!"
                st.session_state.car_toast = True
                st.rerun()
    render_color_sliders(_cor_key)
    with st.container(border=True):
        st.markdown("**Novas Opções**")
        st.caption("Preencha aqui quando selecionar '+ Nova...' no formulário acima.")
        no1, no2, no3 = st.columns(3)
        with no1:
            st.text_input("Nova marca", key="marca_nova_edit")
        with no2:
            st.text_input("Novo fabricante", key="fabricante_novo_edit")
        with no3:
            st.text_input("Nova série", key="serie_nova_edit")


def _render_adicionar() -> None:
    st.subheader("Adicionar carro")
    existing_marcas = sorted(set(c.marca for c in st.session_state.cars if c.marca))
    existing_fabricantes = sorted(set(c.fabricante for c in st.session_state.cars if c.fabricante))
    existing_series = sorted(set(c.serie_tipo for c in st.session_state.cars if c.serie_tipo))

    # --- Foto: upload + swatches à esquerda, preview à direita ---
    with st.container(border=True):
        st.markdown("**Imagem da Miniatura**")
        pc1, pc2 = st.columns(2)
        with pc1:
            file_photo = st.file_uploader("Upload", type=["jpg", "jpeg", "png", "webp"],
                                          key="upload_add", label_visibility="collapsed")
            if file_photo:
                st.session_state._pending_photo = file_photo.getvalue()
            if st.session_state.get("_pending_photo"):
                render_color_picker(
                    st.session_state._pending_photo,
                    bridge_key="__bridge_add__",
                    key="picker_add",
                    cor_key="cor_picker_add",
                )
        with pc2:
            if st.session_state.get("_pending_photo"):
                _b64 = base64.b64encode(st.session_state._pending_photo).decode()
                _live = st.session_state.get("cor_picker_add") or "#808080"
                st.markdown(
                    f"<div style='border:4px solid {_live};border-radius:8px;overflow:hidden'>"
                    f"<img src='data:image/jpeg;base64,{_b64}' style='width:100%;height:320px;object-fit:cover;display:block'></div>",
                    unsafe_allow_html=True)
    with st.form("add_car"):
        l1c1, l1c2 = st.columns(2)
        with l1c1:
            marca_sel = st.selectbox("Marca do carro", existing_marcas + ["+ Nova marca"])
        with l1c2:
            modelo = st.text_input("Modelo")
        l2c1, l2c2 = st.columns(2)
        with l2c1:
            fabricante_sel = st.selectbox("Fabricante da miniatura", existing_fabricantes + ["+ Novo fabricante"])
        with l2c2:
            serie_sel = st.selectbox("Série", existing_series + ["+ Nova série"])
        l3c1, _ = st.columns(2)
        with l3c1:
            ano = st.number_input("Ano", min_value=1950, max_value=2030, value=2024)
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            reserva_add = st.checkbox("Arquivado (não posicionar em expositor)", value=False)
        with fc2:
            desejo_add = st.checkbox("Lista de desejos (não adquirido ainda)", value=False)
        with fc3:
            customizada_add = st.checkbox("Customização", value=False)
        _, add_col, _ = st.columns([2, 1, 2])
        with add_col:
            add = st.form_submit_button("Adicionar", type="primary", use_container_width=True)
        if add:
            marca_nova = st.session_state.get("marca_nova_add", "")
            fabricante_novo = st.session_state.get("fabricante_novo_add", "")
            serie_nova = st.session_state.get("serie_nova_add", "")
            marca = marca_nova.strip() if marca_sel == "+ Nova marca" and marca_nova.strip() else (marca_sel if marca_sel != "+ Nova marca" else "")
            fabricante = fabricante_novo.strip() if fabricante_sel == "+ Novo fabricante" and fabricante_novo.strip() else (fabricante_sel if fabricante_sel != "+ Novo fabricante" else "")
            serie = serie_nova.strip() if serie_sel == "+ Nova série" and serie_nova.strip() else (serie_sel if serie_sel != "+ Nova série" else "")
            if modelo.strip():
                cor_hex = (st.session_state.get("cor_picker_add") or "#808080").upper()
                cor = ""
                foto_path = ""
                if st.session_state.get("_pending_photo"):
                    foto_path = save_photo(st.session_state._pending_photo, modelo.strip())
                insert_car(Car(
                    modelo=modelo.strip(), marca=marca,
                    fabricante=fabricante, ano=ano,
                    cor=cor.strip(), cor_hex=cor_hex, serie_tipo=serie,
                    foto_path=foto_path,
                    reserva=reserva_add,
                    customizada=customizada_add,
                    lista_desejos=desejo_add,
                ))
                st.session_state.pop("_pending_photo", None)
                st.session_state.pop("_pending_picker_color", None)
                st.session_state.pop("_cpicker_picker_add", None)
                st.session_state.pop("cor_picker_add", None)
                refresh()
                st.session_state._car_toast_msg = "Carro adicionado com sucesso!"
                st.session_state.car_toast = True
                st.rerun()
    render_color_sliders("cor_picker_add")
    with st.container(border=True):
        st.markdown("**Novas Opções**")
        st.caption("Preencha aqui quando selecionar '+ Nova...' no formulário acima.")
        no1, no2, no3 = st.columns(3)
        with no1:
            st.text_input("Nova marca", key="marca_nova_add")
        with no2:
            st.text_input("Novo fabricante", key="fabricante_novo_add")
        with no3:
            st.text_input("Nova série", key="serie_nova_add")
