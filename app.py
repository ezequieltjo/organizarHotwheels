import streamlit as st

st.set_page_config(layout="wide", page_title="organizarHotwheels",
                   page_icon=":material/directions_car:")

from storage import init_db
from ui.state import pending_toast, refresh
from ui.theme import render_logo, inject_base_css
from views import ajuda, backup, colecao, desejos, estatisticas, expositores, organizar

init_db()

if "cars" not in st.session_state:
    refresh()

render_logo()

pg = st.navigation([
    st.Page(colecao.render, title="Coleção", icon=":material/directions_car:", url_path="colecao", default=True),
    st.Page(desejos.render, title="Lista de Desejos", icon=":material/favorite:", url_path="desejos"),
    st.Page(estatisticas.render, title="Estatísticas", icon=":material/leaderboard:", url_path="estatisticas"),
    st.Page(expositores.render, title="Expositores", icon=":material/shelves:", url_path="expositores"),
    st.Page(organizar.render, title="Organizar", icon=":material/auto_awesome_motion:", url_path="organizar"),
    st.Page(backup.render, title="Backup", icon=":material/backup:", url_path="backup"),
    st.Page(ajuda.render, title="Como Usar", icon=":material/help:", url_path="como-usar"),
])

inject_base_css()

pg.run()

pending_toast()
