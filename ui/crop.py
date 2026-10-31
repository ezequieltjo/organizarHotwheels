"""Recorte de foto: componente CCv2 com retângulo arrastável + dialog.

O retângulo de corte é ajustável pelas 8 alças e pelo arrasto dentro dele;
as coordenadas (normalizadas 0..1 sobre a imagem exibida) voltam ao Python
via setStateValue no pointerup. Aplicar recorta st.session_state._pending_photo
com PIL e atualiza o preview/form."""
import base64
import io

import streamlit as st
from PIL import Image, ImageOps

# registrado uma vez no import (política CCv2: não re-registrar por chamada)
_CROP = st.components.v2.component(
    "hw_crop",
    html="""
<div id="hw-crop">
  <div id="wrap">
    <img id="foto" alt="" draggable="false" />
    <div id="rect" data-h="move">
      <div data-h="nw" class="h"></div><div data-h="n" class="h"></div>
      <div data-h="ne" class="h"></div><div data-h="e" class="h"></div>
      <div data-h="se" class="h"></div><div data-h="s" class="h"></div>
      <div data-h="sw" class="h"></div><div data-h="w" class="h"></div>
    </div>
  </div>
</div>
""",
    css="""
#hw-crop { text-align: center; }
#wrap { position: relative; display: inline-block; max-width: 100%; touch-action: none; }
#wrap img { display: block; max-width: 100%; max-height: 60vh; border-radius: 6px;
  user-select: none; -webkit-user-drag: none; }
#rect { position: absolute; border: 2px solid var(--st-primary-color);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.45); cursor: move; }
#rect .h { position: absolute; width: 14px; height: 14px; box-sizing: border-box;
  background: var(--st-primary-color); border: 2px solid #fff; border-radius: 3px; }
[data-h="nw"] { top: -8px; left: -8px; cursor: nwse-resize; }
[data-h="n"]  { top: -8px; left: calc(50% - 7px); cursor: ns-resize; }
[data-h="ne"] { top: -8px; right: -8px; cursor: nesw-resize; }
[data-h="e"]  { top: calc(50% - 7px); right: -8px; cursor: ew-resize; }
[data-h="se"] { bottom: -8px; right: -8px; cursor: nwse-resize; }
[data-h="s"]  { bottom: -8px; left: calc(50% - 7px); cursor: ns-resize; }
[data-h="sw"] { bottom: -8px; left: -8px; cursor: nesw-resize; }
[data-h="w"]  { top: calc(50% - 7px); left: -8px; cursor: ew-resize; }
""",
    js="""
export default function (component) {
  const { data, parentElement, setStateValue } = component
  const root = parentElement.querySelector("#hw-crop")
  const img = root.querySelector("#foto")
  const rect = root.querySelector("#rect")
  const MIN = 0.05

  // imagem nova -> zera o recorte (mantém o estado interno entre reruns)
  if (img.getAttribute("src") !== data.src) {
    img.setAttribute("src", data.src)
    root.__box = (data.box && data.box.w) ? { ...data.box } : { x: 0, y: 0, w: 1, h: 1 }
  }
  if (!root.__box) root.__box = { x: 0, y: 0, w: 1, h: 1 }

  const pintar = (b) => {
    rect.style.left = b.x * 100 + "%"
    rect.style.top = b.y * 100 + "%"
    rect.style.width = b.w * 100 + "%"
    rect.style.height = b.h * 100 + "%"
  }
  pintar(root.__box)

  const paraNorm = (cx, cy) => {
    const r = img.getBoundingClientRect()
    return {
      x: Math.min(1, Math.max(0, (cx - r.left) / r.width)),
      y: Math.min(1, Math.max(0, (cy - r.top) / r.height)),
    }
  }

  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v))

  const recalcular = (d, p) => {
    const o = d.orig
    const dx = p.x - d.p0.x
    const dy = p.y - d.p0.y
    const b = { ...o }
    const m = d.mode
    if (m === "move") {
      b.x = clamp(o.x + dx, 0, 1 - o.w)
      b.y = clamp(o.y + dy, 0, 1 - o.h)
      return b
    }
    if (m.includes("e")) b.w = clamp(o.w + dx, MIN, 1 - o.x)
    if (m.includes("s")) b.h = clamp(o.h + dy, MIN, 1 - o.y)
    if (m.includes("w")) {
      b.x = clamp(o.x + dx, 0, o.x + o.w - MIN)
      b.w = o.w + (o.x - b.x)
    }
    if (m.includes("n")) {
      b.y = clamp(o.y + dy, 0, o.y + o.h - MIN)
      b.h = o.h + (o.y - b.y)
    }
    return b
  }

  let drag = null
  root.onpointerdown = (e) => {
    const alvo = e.target.closest("[data-h]")
    if (!alvo) return
    e.preventDefault()
    drag = { mode: alvo.dataset.h, orig: { ...root.__box }, p0: paraNorm(e.clientX, e.clientY) }
    root.setPointerCapture(e.pointerId)
  }
  root.onpointermove = (e) => {
    if (!drag) return
    root.__box = recalcular(drag, paraNorm(e.clientX, e.clientY))
    pintar(root.__box)
  }
  root.onpointerup = () => {
    if (!drag) return
    drag = null
    setStateValue("box", { ...root.__box })
  }
}
""",
)


def botao_cortar(prefix: str) -> None:
    """Botão ✂️ (só com foto carregada) + dialog de recorte sobre _pending_photo."""
    if not st.session_state.get("_pending_photo"):
        return
    if st.button("✂️ Cortar imagem", key=f"cortar_{prefix}"):
        st.session_state.pop(f"_crop_box_{prefix}", None)
        st.session_state["_crop_open"] = prefix
        st.rerun()
    if st.session_state.get("_crop_open") == prefix:
        _dialog(prefix)


def _dialog(prefix: str) -> None:
    @st.dialog("Cortar imagem", width="large")
    def _show() -> None:
        b64 = base64.b64encode(st.session_state._pending_photo).decode()
        key = f"_crop_box_{prefix}"
        _CROP(key=key, data={"src": f"data:image/jpeg;base64,{b64}"},
              on_box_change=lambda: None)
        c1, c2 = st.columns(2)
        if c1.button("✂️ Aplicar recorte", type="primary", use_container_width=True):
            _aplicar(prefix)
        if c2.button("Cancelar", use_container_width=True):
            st.session_state.pop("_crop_open", None)
            st.session_state.pop(key, None)
            st.rerun()

    _show()


def _aplicar(prefix: str) -> None:
    """Recorta _pending_photo conforme a caixa devolvida pelo componente."""
    box = (st.session_state.get(f"_crop_box_{prefix}") or {}).get("box")
    if not box or not box.get("w"):
        return
    foto = st.session_state.pop("_pending_photo")
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(foto)))
    largura, altura = img.size
    caixa = (round(box["x"] * largura), round(box["y"] * altura),
             round((box["x"] + box["w"]) * largura), round((box["y"] + box["h"]) * altura))
    buf = io.BytesIO()
    img.convert("RGB").crop(caixa).save(buf, format="JPEG", quality=90)
    st.session_state._pending_photo = buf.getvalue()
    st.session_state.pop(f"_crop_box_{prefix}", None)
    st.session_state.pop("_crop_open", None)
    st.rerun()
