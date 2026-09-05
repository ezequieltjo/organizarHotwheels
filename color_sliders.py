import streamlit as st

from color_utils import hex_para_rgb, rgb_to_hex, hex_to_hsv_deg, hsv_deg_to_rgb

DEFAULT_COLOR = "#808080"


def _slider_keys(cor_key: str) -> tuple[str, str, str, str, str, str]:
    return (f"{cor_key}__R", f"{cor_key}__G", f"{cor_key}__B",
            f"{cor_key}__H", f"{cor_key}__S", f"{cor_key}__V")


def _on_rgb_change(cor_key: str) -> None:
    """Callback: RGB mudou -> recompõe hex. HSV re-derivado no render, não aqui."""
    rk, gk, bk, _hk, _sk, _vk = _slider_keys(cor_key)
    st.session_state[cor_key] = rgb_to_hex(
        st.session_state[rk], st.session_state[gk], st.session_state[bk])


def _on_hsv_change(cor_key: str) -> None:
    """Callback: HSV mudou -> recompõe hex via HSV->RGB. RGB re-derivado no render."""
    _rk, _gk, _bk, hk, sk, vk = _slider_keys(cor_key)
    r, g, b = hsv_deg_to_rgb(st.session_state[hk], st.session_state[sk], st.session_state[vk])
    st.session_state[cor_key] = rgb_to_hex(r, g, b)


def render_color_sliders(cor_key: str) -> None:
    """Sliders RGB + HSV sincronizados bidirecional, gravam em session_state[cor_key].

    `cor_key` é compartilhado com o st.color_picker nativo e os swatches da foto.
    A escrita em cor_key acontece só nos on_change (entre runs) — nunca após o
    widget instanciado. Se cor_key mudar por fonte externa, sliders resincronizam.
    """
    rk, gk, bk, hk, sk, vk = _slider_keys(cor_key)
    hex_now = st.session_state.get(cor_key) or DEFAULT_COLOR

    # Sliders sempre re-derivados de cor_key (única verdade): color_picker nativo,
    # swatches da foto ou on_change podem mudar cor_key entre runs.
    r0, g0, b0 = hex_para_rgb(hex_now)
    h0, s0, v0 = hex_to_hsv_deg(hex_now)
    st.session_state[rk], st.session_state[gk], st.session_state[bk] = r0, g0, b0
    st.session_state[hk], st.session_state[sk], st.session_state[vk] = h0, s0, v0

    final_hex = st.session_state.get(cor_key) or DEFAULT_COLOR
    with st.container(border=True):
        st.markdown("**Ajuste de Cor**")
        cp_col, hex_col = st.columns([1, 5], gap="small", vertical_alignment="center")
        with cp_col:
            st.color_picker("Cor", key=cor_key, label_visibility="collapsed")
        with hex_col:
            st.markdown(f"<code style='font-size:18px'>{final_hex}</code>", unsafe_allow_html=True)

        col_rgb, col_hsv = st.columns(2)
        with col_rgb:
            st.caption("RGB")
            st.slider("R", 0, 255, key=rk, on_change=_on_rgb_change, args=(cor_key,))
            st.slider("G", 0, 255, key=gk, on_change=_on_rgb_change, args=(cor_key,))
            st.slider("B", 0, 255, key=bk, on_change=_on_rgb_change, args=(cor_key,))
        with col_hsv:
            st.caption("HSV")
            st.slider("H (matiz)", 0, 360, key=hk, on_change=_on_hsv_change, args=(cor_key,))
            st.slider("S (saturação)", 0, 100, key=sk, on_change=_on_hsv_change, args=(cor_key,))
            st.slider("V (luminosidade)", 0, 100, key=vk, on_change=_on_hsv_change, args=(cor_key,))
