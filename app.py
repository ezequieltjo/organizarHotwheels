import streamlit as st

st.set_page_config(layout="wide")

from storage import init_db
from ui.state import refresh
from ui.theme import render_logo, inject_base_css
from views import ajuda, backup, colecao, desejos, estatisticas, expositores, organizar

init_db()

if "cars" not in st.session_state:
    refresh()

render_logo()
inject_base_css()

# --- Main tabs ---
tab1, tab_wish, tab4, tab2, tab3, tab_backup, tab_ajuda = st.tabs(
    ["Coleção", "Lista de Desejos", "Estatísticas", "Expositores", "Organizar", "Backup", "❓ Como Usar"])

with tab1:
    colecao.render()

with tab_wish:
    desejos.render()

with tab4:
    estatisticas.render()

with tab2:
    expositores.render()

with tab3:
    organizar.render()

with tab_backup:
    backup.render()

with tab_ajuda:
    ajuda.render()

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
