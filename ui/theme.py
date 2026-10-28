"""Cores da identidade, logo e CSS global do app."""
import base64

import streamlit as st

from ui.photos import PHOTOS_DIR

# Cores da logo (usadas no tema e nos gráficos)
LOGO_VERMELHO = "#ea1c2c"
LOGO_AMARELO = "#f9d908"
LARANJA = "#e46124"

def render_logo() -> None:
    """Logo no topo da sidebar."""
    _logo_path = PHOTOS_DIR / "logo.png"
    if _logo_path.is_file():
        _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
        st.sidebar.markdown(
            f"<img src='data:image/png;base64,{_logo_b64}' style='width:100%'>",
            unsafe_allow_html=True)


# Grade mobile de cards (ver render_car_list): Streamlit empilha as colunas
# <640px; este seletor casa só com linhas de pares — exatamente 2 colunas
# (:nth-child(2) é a última) e cada uma com um card (data-hw-card, foto_html).
# Desktop usa <div> de 60px sem o marcador; a grade de desejos tem 5 colunas.
_HW_PAIR_SEL = ("[data-testid='stHorizontalBlock']"
                ":has(>[data-testid='stColumn']:first-child [data-hw-card])"
                ":has(>[data-testid='stColumn']:nth-child(2):last-child [data-hw-card])")


def inject_base_css() -> None:
    st.markdown("<style>"
                # header transparente (mantém botões de sidebar/tema acessíveis)
                "header[data-testid='stHeader']{background:transparent}"
                "div[data-testid='stMainBlockContainer']{padding-top:2.75rem!important}"
                # logo (conteúdo do usuário na sidebar) acima da navegação
                "[data-testid='stSidebarContent']{display:flex;flex-direction:column}"
                "[data-testid='stSidebarContent'] [data-testid='stSidebarNav']{order:3}"
                "[data-testid='stSidebarContent'] [data-testid='stSidebarUserContent']{order:2}"
                "[data-testid='stFormSubmitButton'] button{white-space:nowrap}"
                # botão Filtros (popover) na toolbar de linha única não quebra em 2 linhas
                "[data-testid='stPopover'] button{white-space:nowrap}"
                # reset ↺ da toolbar com o mesmo tamanho dos botões de ação
                # (40x40, cantos arredondados); escopo = linha da toolbar: contém
                # stPopover mas nenhuma sub-linha (:not(:has)) — exclui a linha
                # externa lista|form (tem popover nos descendentes e sub-linhas)
                # e o próprio gatilho do popover; seletor descendente pois o botão
                # fica sob stTooltipHoverTarget
                "[data-testid='stHorizontalBlock']"
                ":has([data-testid='stPopover'])"
                ":not(:has([data-testid='stHorizontalBlock']))"
                " button[data-testid=stBaseButton-secondary]:not([data-testid='stPopover'] button)"
                "{width:40px!important;height:40px!important;min-width:40px!important;"
                "border-radius:10px!important;padding:0!important;margin:0 auto!important;"
                "display:flex!important;justify-content:center!important;align-items:center!important}"
                # pills de status (renderizam como stButtonGroup dentro do
                # popover): largura natural, só o texto com padding mínimo,
                # sem esticar para preencher a linha
                "[data-testid='stPopoverBody'] [data-testid='stButtonGroup'] button"
                "{flex:0 0 auto!important;padding:.25rem .45rem!important}"
                "[data-testid='stPopoverBody'] [data-testid='stButtonGroup']"
                "{gap:.35rem!important}"
                ".hw-badges{display:block;margin:.1rem 0;line-height:1.7}"
                ".hw-badge{display:inline-block;font-size:.62rem;font-weight:600;letter-spacing:.03em;"
                "text-transform:uppercase;padding:.12rem .5rem;border-radius:99px;"
                "vertical-align:middle;margin-right:.25rem;border:1px solid transparent}"
                # paleta dos graficos: laranja=arquivado, vermelho=custom, amarelo=repetido
                ".hw-badge-fav{background:#f9d908;color:#3a3000;border-color:#e5c800}"
                ".hw-badge-arq{background:#fae3d8;color:#a8431a;border-color:#e46124}"
                ".hw-badge-custom{background:#fce3e4;color:#c91522;border-color:#ea1c2c}"
                ".hw-badge-rep{background:#fdf6c8;color:#8a7500;border-color:#e5c800}"
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
                # seletor de cores: botão invisível cobre a amostra inteira
                # (clicar na cor aplica; sem botão "Usar" separado)
                "[data-testid='stColumn']:has([data-hw-swatch])"
                " button[kind='primary']:not([data-testid='stForm'] *)"
                "{position:absolute;top:0;left:0;width:100%;height:40px;min-width:0;"
                "opacity:0;border:0;padding:0;cursor:pointer;z-index:9}"
                "[data-testid='stColumn']:has([data-hw-swatch])"
                ">[data-testid='stVerticalBlock']>[data-testid='stElementContainer']"
                ":has(button[kind='primary']){position:static}"
                # o markdown da amostra pintaria acima do botão absoluto e
                # interceptaria o clique — fica clicavelmente transparente
                "[data-testid='stColumn']:has([data-hw-swatch])"
                " [data-testid='stMarkdownContainer']{pointer-events:none}"
                # thumb da lista desktop: maior item da linha, cobre a altura
                # (flex estica coluna -> bloco -> container -> markdown -> thumb)
                "[data-testid='stColumn']:has([data-hw-thumb])"
                " [data-testid='stVerticalBlock']{display:flex!important;flex-direction:column!important;width:100%!important}"
                "[data-testid='stColumn']:has([data-hw-thumb])"
                " [data-testid='stElementContainer']{display:flex!important;flex-direction:column!important;width:100%!important}"
                "[data-testid='stColumn']:has([data-hw-thumb])"
                " [data-testid='stMarkdownContainer']{display:flex!important;flex-direction:column!important;flex:1!important;width:100%!important}"
                # 1ª coluna da linha com largura fixa = thumb (90px) + borda:
                # mata o vão entre a miniatura e o nome e o clique fantasma do
                # zoom nele (o botão do zoom cobre a coluna inteira; nth-child(3)
                # no escopo exclui a linha externa lista|form)
                "[data-testid='stHorizontalBlock']"
                ":has(>[data-testid='stColumn']:first-child [data-hw-thumb])"
                ":has(>[data-testid='stColumn']:nth-child(3):last-child)"
                ">[data-testid='stColumn']:first-child"
                "{flex:0 0 92px!important;width:92px!important;min-width:92px!important;max-width:92px!important}"
                "[data-hw-thumb]{height:100%!important;width:100%!important;max-width:90px;position:relative;min-height:60px}"
                "[data-hw-thumb] img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}"
                # botões de ação (arquivar/editar/excluir): quadrados, cantos
                # arredondados, ícone centralizado; grupo centrado com espaço
                # fixo entre eles (colunas abraçam o botão em vez de esticar)
                # atalho: seletor :has ancestral casava a lista toda e o uploader;
                # escopo agora = sub-bloco de ações da última coluna da linha com thumb
                "[data-testid='stHorizontalBlock']"
                ":has(>[data-testid='stColumn']:first-child [data-hw-thumb])"
                ":has(>[data-testid='stColumn']:nth-child(3):last-child)"
                ">[data-testid='stColumn']:last-child [data-testid='stHorizontalBlock']"
                "{gap:8px!important;justify-content:flex-end!important}"
                "[data-testid='stHorizontalBlock']"
                ":has(>[data-testid='stColumn']:first-child [data-hw-thumb])"
                ":has(>[data-testid='stColumn']:nth-child(3):last-child)"
                ">[data-testid='stColumn']:last-child [data-testid='stHorizontalBlock']"
                ">[data-testid='stColumn']"
                "{flex:0 0 auto!important;width:auto!important;min-width:0!important;margin:0!important}"
                "[data-testid='stHorizontalBlock']"
                ":has(>[data-testid='stColumn']:first-child [data-hw-thumb])"
                ":has(>[data-testid='stColumn']:nth-child(3):last-child)"
                ">[data-testid='stColumn']:last-child [data-testid='stHorizontalBlock']"
                " button[data-testid=stBaseButton-secondary]"
                "{width:40px!important;height:40px!important;min-width:40px!important;"
                "border-radius:10px!important;padding:0!important;margin:0 auto!important;"
                "display:flex!important;justify-content:center!important;align-items:center!important}"
                # zoom (botão invisível) cobre o thumb inteiro
                "[data-testid='stColumn']:has([data-hw-thumb])"
                " button[kind='primary']:not([data-testid='stForm'] *)"
                "{width:100%;height:100%;aspect-ratio:auto}"
                ""
                # grade mobile (pares): botões de ação quadrados também aqui
                f"{_HW_PAIR_SEL} [data-testid='stHorizontalBlock'] button"
                "{width:40px!important;height:40px!important;min-width:40px!important;"
                "border-radius:10px!important;padding:0!important;margin:0 auto!important}"
                # ações da linha (sub-bloco com ≥3 colunas): grupo centrado com
                # espaço fixo; a grade de desejos (2 botões) continua esticada
                f"{_HW_PAIR_SEL} [data-testid='stHorizontalBlock']"
                ":has(>[data-testid='stColumn']:nth-child(3))"
                "{gap:8px!important;justify-content:center!important}"
                f"{_HW_PAIR_SEL} [data-testid='stHorizontalBlock']"
                ":has(>[data-testid='stColumn']:nth-child(3))"
                ">[data-testid='stColumn']"
                "{flex:0 0 auto!important;width:auto!important;margin:0!important}"
                "</style>", unsafe_allow_html=True)
