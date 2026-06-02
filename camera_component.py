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


def render_color_picker(photo_bytes: bytes, bridge_key: str = None, key: str = "color_picker") -> str | None:
    """Show extracted colors from photo as clickable swatches."""
    state_key = f"_cpicker_{key}"

    # Show photo as visual reference
    st.image(photo_bytes, width=300)

    colors = extract_colors(photo_bytes)
    if not colors:
        return st.session_state.get(state_key)

    # Show color swatches
    st.markdown("**Toque na cor que mais se aproxima:**")
    cols = st.columns(min(len(colors), 8))

    for i, hex_c in enumerate(colors[:8]):
        with cols[i]:
            st.markdown(
                f'<div style="width:100%;height:40px;background:{hex_c};'
                f'border-radius:6px;border:2px solid #666"></div>',
                unsafe_allow_html=True,
            )
            if st.button("Usar", key=f"_cpick_{key}_{i}", use_container_width=True):
                st.session_state[state_key] = hex_c
                if key == "picker_edit":
                    st.session_state["cor_picker_edit"] = hex_c
                elif key == "picker_add":
                    st.session_state["cor_picker_add"] = hex_c
                st.rerun()

    return st.session_state.get(state_key)
