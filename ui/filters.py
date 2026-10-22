"""Busca, filtros e ordenação da lista de carros."""
from collections import Counter

import streamlit as st

STATUS_FILTRO_OPTS = ["Todos", "Arquivados", "Não arquivados", "Customizados", "Não customizados", "Repetidos"]

ORDEM_OPTS = [
    "Adição (recentes primeiro)", "Adição (antigos primeiro)",
    "Alfabética (A-Z)", "Alfabética (Z-A)",
    "Ano (crescente)", "Ano (decrescente)",
    "Modificação (recentes primeiro)", "Modificação (antigos primeiro)",
]


def nomes_repetidos(cars: list) -> set:
    """Modelos com nome exatamente igual a outro carro da lista."""
    return {m for m, n in Counter(c.modelo for c in cars).items() if n > 1}


def filter_cars(cars: list, busca: str, marca: str, serie: str,
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
    elif status == "Repetidos":
        rep = nomes_repetidos(cars)
        cars = [c for c in cars if c.modelo in rep]
    return cars


def reset_filtros(prefix: str) -> None:
    """Callback do botão ↺: limpa busca e filtros (roda antes do script)."""
    st.session_state[f"busca_{prefix}"] = ""
    st.session_state[f"filtro_marca_{prefix}"] = "Todas"
    st.session_state[f"filtro_serie_{prefix}"] = "Todas"
    st.session_state[f"filtro_fabricante_{prefix}"] = "Todos"
    st.session_state[f"filtro_status_{prefix}"] = "Todos"


def sort_cars(cars: list, ordem: str) -> list:
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


def list_toolbar(source: list, prefix: str) -> list:
    """Busca + filtros + ordenação. Retorna cars filtrados e ordenados."""
    n_exibidos = len(filter_cars(source,
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
                      on_click=reset_filtros, args=(prefix,))
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
    cars = sort_cars(filter_cars(source, busca, filtro_marca, filtro_serie, filtro_status, filtro_fabricante), ordem)
    return cars
