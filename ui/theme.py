"""Cores da identidade, logo e CSS global do app."""
import base64

import streamlit as st

from ui.photos import PHOTOS_DIR

# Cores da logo (usadas no tema e nos gráficos)
LOGO_VERMELHO = "#ea1c2c"
LOGO_AMARELO = "#f9d908"
LARANJA = "#e46124"

# Altura da faixa do topo ocupada pela logo. Ajuste este único valor.
LOGO_HEADER_HEIGHT = "9rem"


def render_logo() -> None:
    """Logo centralizada no topo."""
    _logo_path = PHOTOS_DIR / "logo.png"
    if _logo_path.is_file():
        _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
        st.markdown(
            f"<div style='text-align:center'>"
            f"<img src='data:image/png;base64,{_logo_b64}' "
            f"style='height:{LOGO_HEADER_HEIGHT};width:auto'></div>",
            unsafe_allow_html=True)


# Grade mobile de cards (ver render_car_list): Streamlit empilha as colunas
# <640px; este seletor casa só com linhas de pares — exatamente 2 colunas
# (:nth-child(2) é a última) e cada uma com um card (data-hw-card, foto_html).
# Desktop usa <div> de 60px sem o marcador; a grade de desejos tem 5 colunas.
_HW_PAIR_SEL = ("[data-testid='stHorizontalBlock']"
                ":has(>[data-testid='stColumn']:first-child [data-hw-card])"
                ":has(>[data-testid='stColumn']:nth-child(2):last-child [data-hw-card])")


def inject_base_css() -> None:
    st.markdown("<style>[data-testid='stTabs'] button{font-size:1.25rem}[data-testid='stFormSubmitButton'] button{white-space:nowrap}"
                "[data-testid='stNumberInputStepUp'] > *,[data-testid='stNumberInputStepDown'] > *{display:none}"
                "[data-testid='stNumberInputStepUp']::after{content:'+';font-size:1rem;font-weight:600;line-height:1}"
                "[data-testid='stNumberInputStepDown']::after{content:'-';font-size:1rem;font-weight:600;line-height:1}"
                f"{_HW_PAIR_SEL}{{flex-direction:row!important;flex-wrap:nowrap!important;align-items:stretch!important}}"
                f"{_HW_PAIR_SEL}>[data-testid='stColumn']{{flex:0 0 calc(50% - .375rem)!important;min-width:0!important}}"
                f"{_HW_PAIR_SEL} [data-testid='stVerticalBlock']{{align-items:stretch!important;height:100%!important}}"
                f"{_HW_PAIR_SEL} [data-testid='stElementContainer']{{width:100%!important}}"
                f"{_HW_PAIR_SEL} [data-testid='stVerticalBlock']>[data-testid='stLayoutWrapper']{{margin-top:auto!important}}"
                f"{_HW_PAIR_SEL} [data-testid='stHorizontalBlock']{{flex-direction:row!important;flex-wrap:nowrap!important}}"
                f"{_HW_PAIR_SEL} [data-testid='stHorizontalBlock']> [data-testid='stColumn']{{flex:1 1 0%!important;min-width:0!important}}"
                f"{_HW_PAIR_SEL} [data-testid='stHorizontalBlock'] [data-testid='stButton']{{width:100%!important}}"
                f"{_HW_PAIR_SEL} [data-testid='stHorizontalBlock'] button{{padding:.4rem 0!important;min-width:0!important;max-width:100%!important;width:100%!important;height:auto!important}}"
                # Zoom da foto: botão invisível cobrindo a foto do card (zoom_btn).
                # Coluna com card = position:relative; o botão do zoom é o único
                # primário fora de um form na coluna (Salvar/Adicionar ficam em forms).
                "[data-testid='stColumn']{position:relative}"
                "[data-testid='stColumn']:has([data-hw-card])"
                " button[kind='primary']:not([data-testid='stForm'] *)"
                "{position:absolute;top:0;left:0;width:100%;aspect-ratio:4/3;min-width:0;"
                "opacity:0;border:0;padding:0;cursor:pointer;z-index:9}"
                # o container do botão é position:relative no CSS do Streamlit e
                # viraria o bloco de referência do absolute — neutraliza
                "[data-testid='stColumn']:has([data-hw-card])"
                ">[data-testid='stVerticalBlock']>[data-testid='stElementContainer']"
                ":has(button[kind='primary']){position:static}"
                # thumb 60x45 fixo (lista desktop): botão do tamanho do thumb
                "[data-testid='stColumn']:has([data-hw-thumb])"
                " button[kind='primary']:not([data-testid='stForm'] *)"
                "{width:60px;height:45px;aspect-ratio:auto}"
                "</style>", unsafe_allow_html=True)
