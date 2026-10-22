"""Aba Lista de Desejos: grid de cards com ➕/🗑️."""
import streamlit as st

from ui.cards import foto_html, is_mobile, maybe_zoom, zoom_btn
from ui.filters import list_toolbar
from views.colecao import act_excluir, act_promover


def wish_card(car) -> None:
    """Card vertical: foto, nome, botões ➕/🗑️ (grid 5-col desktop e 2-col mobile)."""
    st.markdown(foto_html(car), unsafe_allow_html=True)
    zoom_btn(car, "wish")
    st.markdown(
        f"<div style='text-align:center'><b>{car.marca} {car.modelo}</b></div>",
        unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    if b1.button("", icon=":material/add_circle", key=f"wish_add_{car.id}", help="Adicionar à coleção", width="stretch"):
        act_promover(car)
    if b2.button("", icon=":material/delete", key=f"wish_del_{car.id}", help="Remover da lista de desejos", width="stretch"):
        act_excluir(car)


@st.fragment
def wish_grid(source: list) -> None:
    """Matriz 5 colunas (desktop) ou cards 2 colunas (mobile): foto, nome, ➕/🗑️."""
    cars = list_toolbar(source, "wish")
    maybe_zoom()
    if is_mobile():
        per_row = 2
    else:
        per_row = 5
    for i in range(0, len(cars), per_row):
        cols = st.columns(per_row)
        for col, car in zip(cols, cars[i:i + per_row]):
            with col:
                wish_card(car)


def render() -> None:
    desejos = [c for c in st.session_state.cars if c.lista_desejos]
    st.header(f"Lista de Desejos: {len(desejos)} carrinhos")
    if not desejos:
        st.info("Nenhum carro na lista de desejos. Marque 'Lista de desejos' ao adicionar um carro.")
    else:
        wish_grid(desejos)
