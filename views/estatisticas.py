"""Aba Estatísticas: métricas e gráficos por marca/fabricante/série/ano."""
import streamlit as st

from ui.theme import LOGO_VERMELHO, LOGO_AMARELO, LARANJA


def _render_stats(cars: list, cor: str, msg_vazio: str) -> None:
    import pandas as pd
    import plotly.express as px
    if not cars:
        st.info(msg_vazio, icon=":material/leaderboard:")
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


def render() -> None:
    st.header("Estatísticas")

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
