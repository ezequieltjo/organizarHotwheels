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


def _ativos(prefix: str) -> int:
    """Quantidade de filtros (além da busca) diferentes do padrão."""
    defaults = {"filtro_marca": "Todas", "filtro_serie": "Todas",
                "filtro_fabricante": "Todos", "filtro_status": "Todos"}
    return sum(1 for k, d in defaults.items()
               if _um(st.session_state.get(f"{k}_{prefix}", d), d) != d)


def _um(sel, default="Todos"):
    """st.pills pode devolver str ou list — normaliza para um valor."""
    if isinstance(sel, list):
        return sel[0] if sel else default
    return sel or default


def list_toolbar(source: list, prefix: str) -> list:
    """Busca + filtros + ordenação compactos. Retorna cars filtrados e ordenados."""
    n_exibidos = len(filter_cars(source,
                                  st.session_state.get(f"busca_{prefix}", ""),
                                  _um(st.session_state.get(f"filtro_marca_{prefix}", "Todas"), "Todas"),
                                  _um(st.session_state.get(f"filtro_serie_{prefix}", "Todas"), "Todas"),
                                  _um(st.session_state.get(f"filtro_status_{prefix}", "Todos")),
                                  _um(st.session_state.get(f"filtro_fabricante_{prefix}", "Todos"), "Todos")))
    # linha única: busca | ordenar | filtros | reset | contagem
    # (filtros com o mínimo p/ o rótulo "Filtros (n)"; sobra vai p/ a busca)
    c_busca, c_ordem, c_filtro, c_res, c_cnt = st.columns([2.5, 1.8, 1.15, 0.4, 1.15])
    with c_busca:
        busca = st.text_input("Buscar", placeholder="modelo, marca, fabricante ou série...",
                              key=f"busca_{prefix}", label_visibility="collapsed")
    with c_ordem:
        ordem = st.selectbox("Ordenar por", ORDEM_OPTS, key=f"ordem_{prefix}",
                             label_visibility="collapsed")
    with c_filtro:
        n = _ativos(prefix)
        rotulo = f":material/tune: Filtros ({n})" if n else ":material/tune: Filtros"
        with st.popover(rotulo, use_container_width=True):
            filtro_marca = st.selectbox("Marca", ["Todas"] + sorted(set(c.marca for c in source if c.marca)),
                                        key=f"filtro_marca_{prefix}")
            filtro_serie = st.selectbox("Série", ["Todas"] + sorted(set(c.serie_tipo for c in source if c.serie_tipo)),
                                        key=f"filtro_serie_{prefix}")
            filtro_fabricante = st.selectbox("Fabricante", ["Todos"] + sorted(set(c.fabricante for c in source if c.fabricante)),
                                             key=f"filtro_fabricante_{prefix}")
            # width fixo: sem ele o popover cresce para caber tudo em 1 linha;
            # ~330px divide os 6 status em 2 linhas (3+3) com pills no mínimo
            filtro_status = _um(st.pills("Status", STATUS_FILTRO_OPTS,
                                         key=f"filtro_status_{prefix}",
                                         selection_mode="single", width=330))
    with c_res:
        st.button("↺", help="Limpar busca e filtros", key=f"reset_filtros_{prefix}",
                  on_click=reset_filtros, args=(prefix,), width="stretch")
    with c_cnt:
        st.markdown(f"<div style='margin-top:.45rem;font-size:1.05rem;white-space:nowrap'>"
                    f"<b>{n_exibidos}</b> exibidos</div>",
                    unsafe_allow_html=True)

    cars = sort_cars(filter_cars(source, busca, filtro_marca, filtro_serie,
                                 filtro_status, filtro_fabricante), ordem)
    return cars