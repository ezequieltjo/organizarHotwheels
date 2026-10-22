import streamlit as st

st.set_page_config(layout="wide", page_title="organizarHotwheels",
                   page_icon=":material/directions_car:")

from storage import init_db
from ui.state import refresh
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
  `;
  d.head.appendChild(s);
  {_toast_js}
}})();
</script>""", unsafe_allow_javascript=True)
