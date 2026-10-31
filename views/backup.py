"""Aba Backup: exportar/importar ZIP da coleção e apagar tudo."""
import time
import zipfile

import streamlit as st

from backup import export_zip, import_zip, reset_collection
from storage import DB_PATH
from ui.photos import PHOTOS_DIR, THUMBS_DIR
from ui.state import refresh


@st.cache_data
def export_cached(db_mtime: float) -> bytes:
    # ponytail: mtime do DB como chave — toda mudança de coleção escreve no DB
    return export_zip(DB_PATH, PHOTOS_DIR)


def render() -> None:
    st.header("Backup da Coleção")
    st.caption("Exporta banco + fotos num ZIP. Importe em outra máquina para "
               "continuar de onde parou, ou para começar sua própria coleção.")

    st.download_button(
        "⬇️ Exportar coleção (.zip)",
        export_cached(DB_PATH.stat().st_mtime),
        f"colecao_{time.strftime('%Y%m%d')}.zip",
        "application/zip",
        disabled=not st.session_state.cars and not st.session_state.shelves)

    st.divider()

    st.subheader("Importar backup")
    st.warning("Importar **substitui toda a coleção atual** "
               "(carros, expositores e fotos).")
    up_backup = st.file_uploader("ZIP do backup", type=["zip"], key="backup_zip")
    if up_backup and st.button("📥 Importar backup"):
        try:
            n = import_zip(DB_PATH, PHOTOS_DIR, up_backup.getvalue())
        except (ValueError, zipfile.BadZipFile) as e:
            st.error(f"Backup inválido: {e}")
        else:
            export_cached.clear()
            refresh()
            st.session_state.assignment = None
            st.success(f"{n} carros importados!")
            st.rerun()

    st.divider()

    st.subheader("Apagar coleção")
    st.warning("Apaga **todos** os carros, expositores e fotos enviadas, "
               "começando uma base vazia. Baixe um backup antes se quiser guardar.")
    if st.checkbox("Entendo que esta ação apaga tudo", key="reset_confirm"):
        if st.button("🗑️ Apagar coleção"):
            reset_collection(DB_PATH, PHOTOS_DIR, THUMBS_DIR)
            export_cached.clear()
            refresh()
            st.session_state.assignment = None
            st.rerun()
