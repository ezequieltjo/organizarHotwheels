import streamlit as st
from pathlib import Path

st.set_page_config(layout="wide")
from models import Car, ShelfConfig, ParedeConfig, GradientConfig
from storage import (init_db, insert_car, get_all_cars, update_car, delete_car,
                     insert_shelf, get_all_shelves, update_shelf, delete_shelf,
                     clear_positions, apply_positions, get_wall_config, save_wall_config,
                     get_all_disabled_slots, get_disabled_slots, replace_disabled_slots,
                     set_reserva)
from importer import import_file
from organizers import (organize_rainbow, organize_gradient, organize_by_brand,
                        organize_by_fabricante, organize_by_year, organize_random,
                        organize_favorites_first, total_slots)
from visualizer import render_grid
from camera_component import render_color_picker
from thumbs import ensure_thumb
from color_sliders import render_color_sliders
import time
import base64
import io
from PIL import Image

PHOTOS_DIR = Path(__file__).parent / "photos"
PHOTOS_DIR.mkdir(exist_ok=True)
THUMBS_DIR = PHOTOS_DIR / "thumbs"

# Cores da logo (usadas no tema e nos gráficos)
LOGO_VERMELHO = "#ea1c2c"
LOGO_AMARELO = "#f9d908"
LARANJA = "#e46124"

ORGANIZERS = {
    "Arco-íris (por cor)": organize_rainbow,
    "Degradê (moldura)": organize_gradient,
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

def _resolve_photo(path: str) -> Path | None:
    """Resolve a stored foto_path to an existing file Path.

    Handles three stored forms: relative ('photos/x.jpg'), absolute
    (legacy, e.g. 'D:\\Code\\...'), and bare filename. Returns None if no
    matching file exists so the caller falls back to the color swatch.
    """
    if not path:
        return None
    p = Path(path)
    if p.is_absolute():
        candidates = [p, PHOTOS_DIR / p.name]
    else:
        candidates = [PHOTOS_DIR.parent / p, PHOTOS_DIR / p.name]
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def _img_b64(path) -> str:
    """Read resolved image file, return base64 string."""
    resolved = _resolve_photo(str(path))
    if resolved is None:
        raise FileNotFoundError(path)
    return base64.b64encode(resolved.read_bytes()).decode()


def _img_thumb_b64(path) -> str:
    """Base64 do thumbnail (gera sob demanda). Cards usam isto, não a foto original."""
    resolved = _resolve_photo(str(path))
    if resolved is None:
        raise FileNotFoundError(path)
    return base64.b64encode(ensure_thumb(resolved, THUMBS_DIR).read_bytes()).decode()


def _save_photo(photo_bytes: bytes, modelo: str, old_path: str | None = None) -> str:
    """Save photo to disk, return relative path. Remove previous photo when replacing."""
    if photo_bytes[:4] == b"RIFF" and photo_bytes[8:12] == b"WEBP":
        img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        photo_bytes = buf.getvalue()
    ts = int(time.time() * 1000)
    safe = "".join(c if c.isalnum() else "_" for c in modelo)[:30]
    filename = f"{safe}_{ts}.jpg"
    (PHOTOS_DIR / filename).write_bytes(photo_bytes)
    _remove_photo(old_path)
    return f"photos/{filename}"


def _remove_photo(path: str | None) -> None:
    """Delete previous photo file if it lives inside PHOTOS_DIR."""
    resolved = _resolve_photo(path or "")
    if resolved is None:
        return
    try:
        if resolved.is_relative_to(PHOTOS_DIR.resolve()) and resolved.is_file():
            resolved.unlink()
            thumb = THUMBS_DIR / resolved.name
            if thumb.is_file():
                thumb.unlink()
    except OSError:
        pass


STATUS_FILTRO_OPTS = ["Todos", "Arquivados", "Não arquivados", "Customizados", "Não customizados"]


def _filter_cars(cars: list, busca: str, marca: str, serie: str,
                 status: str = "Todos", fabricante: str = "Todos") -> list:
    """Aplica busca textual + filtros de marca, série, status (arquivado/custom) e fabricante."""
    if busca.strip():
        b = busca.lower()
        cars = [c for c in cars if b in c.modelo.lower() or b in c.marca.lower()
                or b in c.fabricante.lower() or b in c.serie_tipo.lower()]
    if marca != "Todas":
        cars = [c for c in cars if c.marca == marca]
    if serie != "Todas":
        cars = [c for c in cars if c.serie_tipo == serie]
    if fabricante != "Todos":
        cars = [c for c in cars if c.fabricante == fabricante]
    if status == "Arquivados":
        cars = [c for c in cars if c.reserva]
    elif status == "Não arquivados":
        cars = [c for c in cars if not c.reserva]
    elif status == "Customizados":
        cars = [c for c in cars if c.customizada]
    elif status == "Não customizados":
        cars = [c for c in cars if not c.customizada]
    return cars


def _reset_filtros(prefix: str) -> None:
    """Callback do botão ↺: limpa busca e filtros (roda antes do script)."""
    st.session_state[f"busca_{prefix}"] = ""
    st.session_state[f"filtro_marca_{prefix}"] = "Todas"
    st.session_state[f"filtro_serie_{prefix}"] = "Todas"
    st.session_state[f"filtro_fabricante_{prefix}"] = "Todos"
    st.session_state[f"filtro_status_{prefix}"] = "Todos"


ORDEM_OPTS = [
    "Adição (recentes primeiro)", "Adição (antigos primeiro)",
    "Alfabética (A-Z)", "Alfabética (Z-A)",
    "Ano (crescente)", "Ano (decrescente)",
    "Modificação (recentes primeiro)", "Modificação (antigos primeiro)",
]


def _ordenar(cars: list, ordem: str) -> list:
    match ordem:
        case "Alfabética (A-Z)":
            return sorted(cars, key=lambda c: c.modelo.lower())
        case "Alfabética (Z-A)":
            return sorted(cars, key=lambda c: c.modelo.lower(), reverse=True)
        case "Ano (crescente)":
            return sorted(cars, key=lambda c: c.ano)
        case "Ano (decrescente)":
            return sorted(cars, key=lambda c: c.ano, reverse=True)
        case "Adição (recentes primeiro)":
            return sorted(cars, key=lambda c: c.created_at or "", reverse=True)
        case "Adição (antigos primeiro)":
            return sorted(cars, key=lambda c: c.created_at or "")
        case "Modificação (recentes primeiro)":
            return sorted(cars, key=lambda c: c.updated_at or "", reverse=True)
        case "Modificação (antigos primeiro)":
            return sorted(cars, key=lambda c: c.updated_at or "")
    return cars


# --- Ações dos botões dos cards (fn(car)) ---

def _act_favorito(car) -> None:
    car.favorito = not car.favorito
    update_car(car)
    refresh()
    st.rerun()


def _act_reserva(car) -> None:
    set_reserva(car.id, not car.reserva)
    refresh()
    st.rerun()


def _act_editar(car) -> None:
    st.session_state.editing_car_id = car.id
    st.session_state.pop("_pending_photo", None)
    st.session_state.pop("_pending_picker_color", None)
    st.session_state.pop("_cpicker_picker_edit", None)
    st.rerun()


def _act_excluir(car) -> None:
    st.session_state.pop("_pending_photo", None)
    st.session_state.pop("_pending_picker_color", None)
    delete_car(car.id)
    refresh()
    st.session_state._car_toast_msg = "Carro removido!"
    st.session_state.car_toast = "delete"
    st.rerun()


def _act_promover(car) -> None:
    """Lista de desejos -> coleção."""
    car.lista_desejos = False
    update_car(car)
    refresh()
    st.session_state._car_toast_msg = "Adicionado à coleção!"
    st.session_state.car_toast = True
    st.rerun()


COLECAO_ACTIONS = [
    ("⭐", None, _act_favorito),
    (lambda c: "📦" if c.reserva else "📭",
     "Marcar/desmarcar arquivado (não posicionar)", _act_reserva),
    ("✏️", None, _act_editar),
    ("🗑️", None, _act_excluir),
]

@st.fragment
def _wish_grid(source: list) -> None:
    """Matrix 5 colunas: foto, nome+marca, botões ➕/🗑️."""
    cars = _list_toolbar(source, "wish")
    for i in range(0, len(cars), 5):
        cols = st.columns(5)
        for col, car in zip(cols, cars[i:i + 5]):
            with col:
                if _resolve_photo(car.foto_path) is not None:
                    st.markdown(
                        f"<div style='border:3px solid {car.cor_hex};border-radius:6px;overflow:hidden'>"
                        f"<img src='data:image/jpeg;base64,{_img_thumb_b64(car.foto_path)}' "
                        f"style='width:100%;aspect-ratio:4/3;object-fit:cover;display:block'></div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<div style='width:100%;aspect-ratio:4/3;background:{car.cor_hex};"
                        f"border-radius:4px'></div>",
                        unsafe_allow_html=True)
                st.markdown(
                    f"<div style='text-align:center'><b>{car.marca} {car.modelo}</b></div>",
                    unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button("➕", key=f"wish_add_{car.id}", help="Adicionar à coleção"):
                    _act_promover(car)
                if b2.button("🗑️", key=f"wish_del_{car.id}", help="Remover da lista de desejos"):
                    _act_excluir(car)


def _list_toolbar(source: list, prefix: str) -> list:
    """Busca + filtros + ordenação. Retorna cars filtrados e ordenados."""
    n_exibidos = len(_filter_cars(source,
                                  st.session_state.get(f"busca_{prefix}", ""),
                                  st.session_state.get(f"filtro_marca_{prefix}", "Todas"),
                                  st.session_state.get(f"filtro_serie_{prefix}", "Todas"),
                                  st.session_state.get(f"filtro_status_{prefix}", "Todos"),
                                  st.session_state.get(f"filtro_fabricante_{prefix}", "Todos")))
    sb_col, cnt_col = st.columns([4, 1])
    with sb_col:
        busca = st.text_input("Buscar", placeholder="modelo, marca, fabricante ou série...", key=f"busca_{prefix}")
    with cnt_col:
        cc1, cc2 = st.columns([1, 1.1], gap="small")
        with cc1:
            st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            st.button("↺", help="Limpar busca e filtros", key=f"reset_filtros_{prefix}",
                      on_click=_reset_filtros, args=(prefix,))
        with cc2:
            st.markdown(
                f"<div style='margin-top:2.05rem;margin-left:-0.6rem;font-size:1.25rem'>"
                f"<b>{n_exibidos}</b> exibidos</div>",
                unsafe_allow_html=True)

    fc1, fc2, fc3, fc4, fc5 = st.columns([1.3, 1, 1.1, 1, 1])
    with fc1:
        ordem = st.selectbox("Ordenar por", ORDEM_OPTS, key=f"ordem_{prefix}")
    with fc2:
        filtro_marca = st.selectbox("Filtrar marca", ["Todas"] + sorted(set(c.marca for c in source if c.marca)), key=f"filtro_marca_{prefix}")
    with fc3:
        filtro_serie = st.selectbox("Filtrar série", ["Todas"] + sorted(set(c.serie_tipo for c in source if c.serie_tipo)), key=f"filtro_serie_{prefix}")
    with fc4:
        filtro_fabricante = st.selectbox("Fabricante", ["Todos"] + sorted(set(c.fabricante for c in source if c.fabricante)), key=f"filtro_fabricante_{prefix}")
    with fc5:
        filtro_status = st.selectbox("Status", STATUS_FILTRO_OPTS, key=f"filtro_status_{prefix}")
    cars = _ordenar(_filter_cars(source, busca, filtro_marca, filtro_serie, filtro_status, filtro_fabricante), ordem)
    return cars


@st.fragment
def _render_car_list(source: list, prefix: str, actions: list) -> None:
    """Cards em linhas. actions: (emoji|fn(car), help, fn(car))."""
    for car in _list_toolbar(source, prefix):
        with st.container():
            col1, col2, col3 = st.columns([1, 6, 2])
            with col1:
                if _resolve_photo(car.foto_path) is not None:
                    st.markdown(
                        f"<div style='border:3px solid {car.cor_hex};border-radius:6px;overflow:hidden;width:60px;height:45px'>"
                        f"<img src='data:image/jpeg;base64,{_img_thumb_b64(car.foto_path)}' style='width:100%;height:100%;object-fit:cover'></div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='width:60px;height:45px;background:{car.cor_hex};border-radius:4px'></div>",
                                unsafe_allow_html=True)
            with col2:
                fav = "★ " if car.favorito else ""
                reserva_marker = "📦 " if car.reserva else ""
                customizada_marker = "🖌️ " if car.customizada else ""
                st.write(f"**{reserva_marker}{customizada_marker}{car.marca} {fav}{car.modelo}** — {car.fabricante or '?'} | {car.serie_tipo}")
            with col3:
                btns = st.columns(len(actions))
                for i, (btn_col, (emoji, help_text, fn)) in enumerate(zip(btns, actions)):
                    label = emoji(car) if callable(emoji) else emoji
                    if btn_col.button(label, key=f"act_{prefix}_{i}_{car.id}", help=help_text):
                        fn(car)


# --- Logo centralizada no topo ---
# Altura da faixa do topo ocupada pela logo. Ajuste este único valor.
LOGO_HEADER_HEIGHT = "9rem"
_logo_path = PHOTOS_DIR / "logo.png"
if _logo_path.is_file():
    _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
    st.markdown(
        f"<div style='text-align:center'>"
        f"<img src='data:image/png;base64,{_logo_b64}' "
        f"style='height:{LOGO_HEADER_HEIGHT};width:auto'></div>",
        unsafe_allow_html=True)

# --- Main tabs ---
tab1, tab_wish, tab4, tab2, tab3 = st.tabs(
    ["Coleção", "Lista de Desejos", "Estatísticas", "Expositores", "Organizar"])
st.markdown("<style>[data-testid='stTabs'] button{font-size:1.25rem}</style>", unsafe_allow_html=True)

with tab1:
    colecao = [c for c in st.session_state.cars if not c.lista_desejos]
    n_reservas = sum(1 for c in colecao if c.reserva)
    st.header(f"Coleção: {len(colecao)} carrinhos"
              + (f" ({n_reservas} arquivados)" if n_reservas else ""))

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
        _render_car_list(colecao, "cars", COLECAO_ACTIONS)
    with c2:
        if editing_car:
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
                    elif (_existing := _resolve_photo(editing_car.foto_path)) is not None:
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
                l2c1, l2c2, l2c3 = st.columns([1.4, 1.1, 0.6])
                with l2c1:
                    fab_opts = existing_fabricantes + ["+ Novo fabricante"]
                    fab_idx = fab_opts.index(editing_car.fabricante) if editing_car.fabricante in fab_opts else 0
                    fabricante_sel = st.selectbox("Fabricante da miniatura", fab_opts, index=fab_idx, key="edit_fab_sel")
                with l2c2:
                    serie_opts = existing_series + ["+ Nova série"]
                    serie_idx = serie_opts.index(editing_car.serie_tipo) if editing_car.serie_tipo in serie_opts else 0
                    serie_sel = st.selectbox("Série", serie_opts, index=serie_idx, key="edit_serie_sel")
                with l2c3:
                    ano = st.number_input("Ano", min_value=1950, max_value=2030, value=editing_car.ano)
                fc1, fc2, _ = st.columns(3)
                with fc1:
                    reserva_edit = st.checkbox("Arquivado (não posicionar em expositor)", value=editing_car.reserva)
                with fc2:
                    customizada_edit = st.checkbox("Customização", value=editing_car.customizada)
                _, btn_col, _ = st.columns([2, 1, 2])
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
                            foto_path = _save_photo(
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
                        if reserva_edit and editing_car.expositor_id is not None:
                            update_car(editing_car)
                            set_reserva(editing_car.id, True)  # atomic clear of position
                        else:
                            update_car(editing_car)
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
        else:
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
                l2c1, l2c2, l2c3 = st.columns([1.4, 1.1, 0.6])
                with l2c1:
                    fabricante_sel = st.selectbox("Fabricante da miniatura", existing_fabricantes + ["+ Novo fabricante"])
                with l2c2:
                    serie_sel = st.selectbox("Série", existing_series + ["+ Nova série"])
                with l2c3:
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
                            foto_path = _save_photo(st.session_state._pending_photo, modelo.strip())
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

with tab_wish:
    desejos = [c for c in st.session_state.cars if c.lista_desejos]
    st.header(f"Lista de Desejos: {len(desejos)} carrinhos")
    if not desejos:
        st.info("Nenhum carro na lista de desejos. Marque 'Lista de desejos' ao adicionar um carro.")
    else:
        _wish_grid(desejos)

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

with tab3:
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

with tab4:
    st.header("Estatísticas")
    import pandas as pd
    import plotly.express as px

    def _render_stats(cars: list, cor: str, msg_vazio: str) -> None:
        if not cars:
            st.info(msg_vazio)
            return
        df = pd.DataFrame([{
            "marca": c.marca,
            "fabricante": c.fabricante,
            "serie_tipo": c.serie_tipo,
            "ano": c.ano,
        } for c in cars])
        # Vazios viram rótulo legível; ano 0 = sem ano.
        for col in ("marca", "fabricante", "serie_tipo"):
            df[col] = df[col].replace("", "(sem)")
        df["ano"] = df["ano"].astype(str).replace("0", "(sem ano)")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de carros", len(df))
        m2.metric("Marcas", df["marca"].nunique())
        m3.metric("Fabricantes", df["fabricante"].nunique())
        m4.metric("Séries", df["serie_tipo"].nunique())

        st.divider()

        def _bar(field: str, title: str, sort_index: bool = False) -> None:
            counts = df[field].value_counts()
            if sort_index:
                counts = counts.sort_index()
            counts = counts.reset_index()
            counts.columns = [field, "quantidade"]
            fig = px.bar(counts, x=field, y="quantidade", title=title,
                         text="quantidade", color_discrete_sequence=[cor])
            fig.update_layout(showlegend=False, xaxis_tickangle=-45, height=380)
            st.plotly_chart(fig, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            _bar("marca", "Carros por marca")
            _bar("serie_tipo", "Carros por série")
        with col_b:
            _bar("fabricante", "Carros por fabricante")
            _bar("ano", "Carros por ano", sort_index=True)

    st.subheader("Coleção")
    _render_stats(
        [c for c in st.session_state.cars if not c.lista_desejos and not c.reserva],
        LOGO_VERMELHO, "Nenhum carro na coleção ainda.")

    st.subheader("Arquivados")
    _render_stats(
        [c for c in st.session_state.cars if c.reserva and not c.lista_desejos],
        LARANJA, "Nenhum carro arquivado.")

    st.subheader("Lista de Desejos")
    _render_stats(
        [c for c in st.session_state.cars if c.lista_desejos],
        LOGO_AMARELO, "Nenhum carro na lista de desejos.")

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
    header[data-testid="stHeader"]{{display:none!important;}}
    div[data-testid="stMainBlockContainer"]{{padding-top:1rem!important;}}
    .car-actions-row{{display:flex!important;gap:6px!important;justify-content:center!important;align-items:center!important;}}
    .car-actions-row > div{{flex:0 0 30px!important;width:30px!important;padding:0!important;margin:0!important;}}
    .car-actions-row button{{display:flex!important;justify-content:center!important;align-items:center!important;font-size:1.1rem!important;padding:0!important;width:30px!important;height:30px!important;min-width:30px!important;max-width:30px!important;border-radius:6px!important;margin:0 auto!important;line-height:1!important;}}
  `;
  d.head.appendChild(s);
  function markButtons(){{
    d.querySelectorAll('button').forEach(function(b){{
      var t=b.textContent.trim();
      if((t==='⭐'||t==='📦'||t==='📭'||t==='✏️'||t==='🗑️'||t==='➕')&&b.closest('[data-testid="stColumn"]')){{
        var col=b.closest('[data-testid="stColumn"]');
        var row=col.parentElement;
        if(row&&row.getAttribute('data-testid')==='stHorizontalBlock'){{
          row.classList.add('car-actions-row');
        }}
      }}
    }});
  }}
  markButtons();
  setInterval(markButtons,300);
  {_toast_js}
}})();
</script>""", unsafe_allow_javascript=True)
