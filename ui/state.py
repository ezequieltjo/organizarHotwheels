"""Estado de sessão compartilhado entre as páginas."""
import streamlit as st

from storage import get_all_cars, get_all_shelves, get_wall_config, get_all_disabled_slots


def refresh() -> None:
    """Recarrega carros, expositores, parede e vagas bloqueadas do banco."""
    st.session_state.cars = get_all_cars()
    st.session_state.shelves = get_all_shelves()
    st.session_state.wall = get_wall_config()
    st.session_state.disabled = get_all_disabled_slots()
