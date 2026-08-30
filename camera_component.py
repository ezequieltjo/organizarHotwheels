import streamlit as st
from PIL import Image
import io
from collections import Counter


def extract_colors(photo_bytes: bytes, n: int = 8) -> list[str]:
    """Extract dominant colors from a photo."""
    img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    img = img.resize((80, 80))

    pixels = list(img.getdata())
    # Quantize to reduce noise
    quantized = [
        (min(r // 32 * 32 + 16, 255), min(g // 32 * 32 + 16, 255), min(b // 32 * 32 + 16, 255))
        for r, g, b in pixels
    ]

    counter = Counter(quantized)
    result = []
    for (r, g, b), _ in counter.most_common(n * 5):
        if not any(abs(r - er) + abs(g - eg) + abs(b - eb) < 50 for er, eg, eb in result):
            result.append((r, g, b))
        if len(result) >= n:
            break

    return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in result]


def render_color_picker(photo_bytes: bytes, bridge_key: str = None, key: str = "color_picker", cor_key: str = None) -> str | None:
    """Show extracted colors from photo as clickable swatches (2 linhas x 4)."""
    state_key = f"_cpicker_{key}"

    colors = extract_colors(photo_bytes)
    if not colors:
        return st.session_state.get(state_key)

    # Show color swatches
    st.markdown("**Toque na cor que mais se aproxima:**")
    for row in range(2):
        cols = st.columns(4)
        for i, hex_c in enumerate(colors[row * 4:(row + 1) * 4]):
            with cols[i]:
                st.markdown(
                    f'<div style="width:100%;height:40px;background:{hex_c};'
                    f'border-radius:6px;border:2px solid #666"></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Usar", key=f"_cpick_{key}_{row * 4 + i}", width="stretch"):
                    st.session_state[state_key] = hex_c
                    if cor_key:
                        st.session_state[cor_key] = hex_c
                    st.rerun()

    return st.session_state.get(state_key)
