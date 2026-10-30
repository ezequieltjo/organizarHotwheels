"""Componentes de card do carro: foto, zoom, ações, lista desktop/mobile."""
import base64

import streamlit as st

from ui.filters import list_toolbar, nomes_repetidos
from ui.photos import img_thumb_url, resolve_photo

TAM_PAGINA = 60


def is_mobile() -> bool:
    """True em celular (User-Agent com 'Mobi'). iPad não tem 'Mobi' — recebe layout desktop."""
    ua = st.context.headers.get("User-Agent") or ""
    return "Mobi" in ua


def foto_html(car) -> str:
    """HTML da foto em 4:3 com borda na cor do carro; swatch da cor se sem foto.

    data-hw-card marca o card para o JS do layout mobile (hw_pair_row_css).
    Foto por URL estática com loading=lazy: o rerun só transmite o endereço."""
    url = img_thumb_url(car.foto_path)
    if url is not None:
        return (f"<div data-hw-card style='border:3px solid {car.cor_hex};border-radius:6px;overflow:hidden'>"
                f"<img src='{url}' loading='lazy' "
                f"style='width:100%;aspect-ratio:4/3;object-fit:cover;display:block'></div>")
    return (f"<div data-hw-card style='border:3px solid {car.cor_hex};border-radius:6px;"
            f"overflow:hidden;aspect-ratio:4/3;background:{car.cor_hex}'></div>")


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


def badges_html(car, repetidos: set) -> str:
    """Pills coloridas: arquivado · custom · repetido (★ favorito dormente)."""
    pills = []
    if car.reserva:
        pills.append('<span class="hw-badge hw-badge-arq" title="Arquivado (não posicionado)">arquivado</span>')
    if car.customizada:
        pills.append('<span class="hw-badge hw-badge-custom" title="Customizado">custom</span>')
    if car.modelo in repetidos:
        pills.append('<span class="hw-badge hw-badge-rep" title="Modelo repetido na coleção">repetido</span>')
    if not pills:
        return ""
    return '<span class="hw-badges">' + "".join(pills) + "</span>"


def render_car_card(car, repetidos: set, prefix: str, actions: list) -> None:
    """Card vertical p/ mobile: foto grande em cima, texto central, botões em linha."""
    st.markdown(foto_html(car), unsafe_allow_html=True)
    zoom_btn(car, "card")
    st.markdown(
        f"<div style='text-align:center'><b>{car.marca} {car.modelo}</b> — "
        f"{car.fabricante or '?'} | {car.serie_tipo}"
        f"{badges_html(car, repetidos)}</div>",
        unsafe_allow_html=True)
    btns = st.columns(len(actions))
    for i, (btn_col, (icon, help_text, fn)) in enumerate(zip(btns, actions)):
        ic = icon(car) if callable(icon) else icon
        if btn_col.button("", icon=ic, key=f"act_{prefix}_{i}_{car.id}", help=help_text,
                          width="stretch"):
            fn(car)


def _paginar(prefix: str, total: int) -> int:
    """Seletor de página acima da lista; reseta para 1 ao mudar busca/filtro/ordem.

    Retorna a página atual (sempre <= nº de páginas)."""
    chaves = ("busca", "filtro_marca", "filtro_serie", "filtro_fabricante",
              "filtro_status", "ordem")
    assinatura = tuple(st.session_state.get(f"{k}_{prefix}") for k in chaves)
    n_paginas = max(1, -(-total // TAM_PAGINA))
    if assinatura != st.session_state.get(f"_pag_sig_{prefix}"):
        st.session_state[f"pagina_{prefix}"] = 1
        st.session_state[f"_pag_sig_{prefix}"] = assinatura
    pagina = min(st.session_state.get(f"pagina_{prefix}") or 1, n_paginas)
    if n_paginas > 1:
        st.session_state.setdefault(f"pagina_{prefix}", pagina)
        st.segmented_control("Página", range(1, n_paginas + 1),
                             key=f"pagina_{prefix}", label_visibility="collapsed")
    return pagina


@st.fragment
def render_car_list(source: list, prefix: str, actions: list) -> None:
    """Cards em linhas (desktop) ou grade 2 colunas (mobile), paginados.

    actions: (emoji|fn(car), help, fn(car)). Fragment: busca, filtros e página
    rerunam só este bloco; as ações de linha chamam st.rerun() padrão
    (scope='app') porque atualizam contagens do cabeçalho."""
    repetidos = nomes_repetidos(source)
    cars = list_toolbar(source, prefix)
    maybe_zoom()
    pagina = _paginar(prefix, len(cars))
    cars = cars[(pagina - 1) * TAM_PAGINA: pagina * TAM_PAGINA]
    if is_mobile():
        for i in range(0, len(cars), 2):
            cols = st.columns(2)
            for col, car in zip(cols, cars[i:i + 2]):
                with col:
                    render_car_card(car, repetidos, prefix, actions)
        return
    for car in cars:
        with st.container():
            # ações na 3ª coluna estreita (só o necessário p/ 3 botões de 40px),
            # alinhadas à direita pelo CSS e encostadas no formulário
            col1, col2, col3 = st.columns([1.3, 5.5, 1.7])
            with col1:
                url = img_thumb_url(car.foto_path)
                if url is not None:
                    st.markdown(
                        f"<div data-hw-card data-hw-thumb style='border:3px solid {car.cor_hex};border-radius:6px;overflow:hidden;min-height:60px;height:100%;box-sizing:border-box'>"
                        f"<img src='{url}' loading='lazy' style='width:100%;height:100%;object-fit:cover'></div>",
                        unsafe_allow_html=True)
                    zoom_btn(car, "row")
                else:
                    # margin-bottom replica o slot do botão de zoom (gap de 16px
                    # do bloco vertical) — sem ela a linha fica mais baixa que
                    # o quadrado de 60px e ele encosta no card seguinte
                    st.markdown(
                        f"<div data-hw-card data-hw-thumb style='border:3px solid {car.cor_hex};"
                        f"border-radius:6px;overflow:hidden;box-sizing:border-box;"
                        f"background:{car.cor_hex};min-height:60px;height:100%;"
                        f"margin-bottom:1rem'></div>",
                        unsafe_allow_html=True)
            with col2:
                st.markdown(
                    f"**{car.marca} {car.modelo}** — {car.fabricante or '?'} | "
                    f"{car.serie_tipo}{badges_html(car, repetidos)}",
                    unsafe_allow_html=True)
            with col3:
                btns = st.columns(len(actions))
                for i, (btn_col, (icon, help_text, fn)) in enumerate(zip(btns, actions)):
                    ic = icon(car) if callable(icon) else icon
                    if btn_col.button("", icon=ic, key=f"act_{prefix}_{i}_{car.id}", help=help_text,
                                      width="stretch"):
                        fn(car)
