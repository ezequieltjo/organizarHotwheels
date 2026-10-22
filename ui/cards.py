"""Componentes de card do carro: foto, zoom, ações, lista desktop/mobile."""
import base64

import streamlit as st

from ui.filters import list_toolbar, nomes_repetidos
from ui.photos import img_thumb_b64, resolve_photo


def is_mobile() -> bool:
    """True em celular (User-Agent com 'Mobi'). iPad não tem 'Mobi' — recebe layout desktop."""
    ua = st.context.headers.get("User-Agent") or ""
    return "Mobi" in ua


def foto_html(car) -> str:
    """HTML da foto em 4:3 com borda na cor do carro; swatch da cor se sem foto.

    data-hw-card marca o card para o JS do layout mobile (hw_pair_row_css)."""
    if resolve_photo(car.foto_path) is not None:
        return (f"<div data-hw-card style='border:3px solid {car.cor_hex};border-radius:6px;overflow:hidden'>"
                f"<img src='data:image/jpeg;base64,{img_thumb_b64(car.foto_path)}' "
                f"style='width:100%;aspect-ratio:4/3;object-fit:cover;display:block'></div>")
    return (f"<div data-hw-card style='width:100%;aspect-ratio:4/3;background:{car.cor_hex};"
            f"border-radius:4px'></div>")


def act_zoom(car) -> None:
    if resolve_photo(car.foto_path) is not None:
        st.session_state["_zoom_id"] = car.id


def zoom_dialog(car) -> None:
    titulo = f"{car.marca} {car.modelo}".strip()
    if car.ano:
        titulo += f" ({car.ano})"
    if car.serie_tipo:
        titulo += f" — {car.serie_tipo}"

    @st.dialog(titulo, width="large")
    def _show() -> None:
        resolved = resolve_photo(car.foto_path)
        b64 = base64.b64encode(resolved.read_bytes()).decode()
        st.markdown(
            f"<div style='display:flex;justify-content:center'>"
            f"<img src='data:image/jpeg;base64,{b64}' "
            f"style='max-width:100%;max-height:70vh;object-fit:contain;border-radius:8px'></div>",
            unsafe_allow_html=True)

    _show()


def maybe_zoom() -> None:
    """Abre o dialog de zoom se um botão de zoom foi clicado (chamar dentro do fragment)."""
    zoom_id = st.session_state.pop("_zoom_id", None)
    if zoom_id is None:
        return
    car = next((c for c in st.session_state.cars if c.id == zoom_id), None)
    if car:
        zoom_dialog(car)


def zoom_btn(car, prefix: str) -> None:
    """Botão invisível sobreposto à foto via CSS (ver regra :has no inject_base_css)."""
    if resolve_photo(car.foto_path) is None:
        return
    st.button("🔍", key=f"zoom_{prefix}_{car.id}",
              on_click=act_zoom, args=(car,), type="primary")


def render_car_card(car, repetidos: set, prefix: str, actions: list) -> None:
    """Card vertical p/ mobile: foto grande em cima, texto central, botões em linha."""
    st.markdown(foto_html(car), unsafe_allow_html=True)
    zoom_btn(car, "card")
    fav = "★ " if car.favorito else ""
    reserva_marker = "📦 " if car.reserva else ""
    customizada_marker = "🖌️ " if car.customizada else ""
    repetido_marker = "🔁 " if car.modelo in repetidos else ""
    st.markdown(
        f"<div style='text-align:center'><b>{reserva_marker}{customizada_marker}{repetido_marker}"
        f"{car.marca} {fav}{car.modelo}</b><br>"
        f"<small>{car.fabricante or '?'} | {car.serie_tipo}</small></div>",
        unsafe_allow_html=True)
    btns = st.columns(len(actions))
    for i, (btn_col, (emoji, help_text, fn)) in enumerate(zip(btns, actions)):
        label = emoji(car) if callable(emoji) else emoji
        if btn_col.button(label, key=f"act_{prefix}_{i}_{car.id}", help=help_text):
            fn(car)


def render_car_list(source: list, prefix: str, actions: list) -> None:
    """Cards em linhas (desktop) ou grade 2 colunas (mobile). actions: (emoji|fn(car), help, fn(car))."""
    repetidos = nomes_repetidos(source)
    cars = list_toolbar(source, prefix)
    maybe_zoom()
    if is_mobile():
        for i in range(0, len(cars), 2):
            cols = st.columns(2)
            for col, car in zip(cols, cars[i:i + 2]):
                with col:
                    render_car_card(car, repetidos, prefix, actions)
        return
    for car in cars:
        with st.container():
            col1, col2, col3 = st.columns([1, 6, 2])
            with col1:
                if resolve_photo(car.foto_path) is not None:
                    st.markdown(
                        f"<div data-hw-card data-hw-thumb style='border:3px solid {car.cor_hex};border-radius:6px;overflow:hidden;width:60px;height:45px'>"
                        f"<img src='data:image/jpeg;base64,{img_thumb_b64(car.foto_path)}' style='width:100%;height:100%;object-fit:cover'></div>",
                        unsafe_allow_html=True)
                    zoom_btn(car, "row")
                else:
                    st.markdown(f"<div style='width:60px;height:45px;background:{car.cor_hex};border-radius:4px'></div>",
                                unsafe_allow_html=True)
            with col2:
                fav = "★ " if car.favorito else ""
                reserva_marker = "📦 " if car.reserva else ""
                customizada_marker = "🖌️ " if car.customizada else ""
                repetido_marker = "🔁 " if car.modelo in repetidos else ""
                st.write(f"**{reserva_marker}{customizada_marker}{repetido_marker}{car.marca} {fav}{car.modelo}** — {car.fabricante or '?'} | {car.serie_tipo}")
            with col3:
                btns = st.columns(len(actions))
                for i, (btn_col, (emoji, help_text, fn)) in enumerate(zip(btns, actions)):
                    label = emoji(car) if callable(emoji) else emoji
                    if btn_col.button(label, key=f"act_{prefix}_{i}_{car.id}", help=help_text):
                        fn(car)
