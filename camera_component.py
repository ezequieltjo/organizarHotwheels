import base64
import streamlit.components.v2 as components

color_picker_component = components.component(
    name="pixel_color_picker",
    html="""
    <div class="picker-wrap" id="picker-wrap">
      <canvas id="photo-canvas"></canvas>
      <svg id="crosshair" class="crosshair" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="15" fill="none" stroke="white" stroke-width="2"/>
        <line x1="20" y1="5" x2="20" y2="35" stroke="white" stroke-width="1"/>
        <line x1="5" y1="20" x2="35" y2="20" stroke="white" stroke-width="1"/>
        <circle cx="20" cy="20" r="3" fill="white" opacity="0.5"/>
      </svg>
      <div id="color-preview" class="color-preview" style="display:none">
        <div id="swatch" class="swatch"></div>
        <span id="hex-label"></span>
      </div>
      <div class="btn-row">
        <button id="confirm-btn" style="display:none">Confirmar Cor</button>
      </div>
    </div>
    """,
    css="""
    .picker-wrap { position: relative; display: inline-block; max-width: 100%; }
    #photo-canvas {
      max-width: 100%; height: auto; border-radius: 6px;
      cursor: crosshair; display: block;
    }
    .crosshair {
      position: absolute; width: 40px; height: 40px; pointer-events: none;
      display: none; transform: translate(-50%, -50%);
      filter: drop-shadow(0 0 2px rgba(0,0,0,0.8));
    }
    .color-preview {
      display: flex; align-items: center; gap: 8px; margin-top: 8px;
      font-family: monospace; font-size: 14px;
    }
    .swatch {
      width: 32px; height: 32px; border-radius: 4px;
      border: 2px solid #ccc; flex-shrink: 0;
    }
    .btn-row { margin-top: 8px; }
    #confirm-btn {
      padding: 6px 16px; border: none; border-radius: 6px; cursor: pointer;
      background: var(--st-primary-color); color: #fff; font-size: 14px;
    }
    #confirm-btn:hover { opacity: 0.85; }
    """,
    js="""
    export default function({ parentElement, setStateValue, data }) {
      const canvas = parentElement.querySelector("#photo-canvas");
      const ctx = canvas.getContext("2d");
      const crosshair = parentElement.querySelector("#crosshair");
      const preview = parentElement.querySelector("#color-preview");
      const swatch = parentElement.querySelector("#swatch");
      const hexLabel = parentElement.querySelector("#hex-label");
      const confirmBtn = parentElement.querySelector("#confirm-btn");

      let selectedColor = null;

      function pickColor(e) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const sx = canvas.width / rect.width;
        const sy = canvas.height / rect.height;
        const cx = Math.min(canvas.width - 1, Math.max(0, Math.floor(x * sx)));
        const cy = Math.min(canvas.height - 1, Math.max(0, Math.floor(y * sy)));

        crosshair.style.left = x + "px";
        crosshair.style.top = y + "px";
        crosshair.style.display = "block";

        const px = ctx.getImageData(cx, cy, 1, 1).data;
        const hex = "#" + [px[0], px[1], px[2]]
          .map(v => v.toString(16).padStart(2, "0")).join("");
        swatch.style.backgroundColor = hex;
        hexLabel.textContent = hex.toUpperCase();
        preview.style.display = "flex";
        return hex;
      }

      canvas.addEventListener("mousemove", (e) => { pickColor(e); });
      canvas.addEventListener("click", (e) => {
        selectedColor = pickColor(e);
        confirmBtn.style.display = "inline-block";
      });
      confirmBtn.addEventListener("click", () => {
        if (selectedColor) setStateValue("color", selectedColor.toUpperCase());
      });

      if (data && data.photo) {
        const img = new Image();
        img.onload = () => {
          const maxW = 400;
          const scale = Math.min(1, maxW / img.width);
          canvas.width = Math.floor(img.width * scale);
          canvas.height = Math.floor(img.height * scale);
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        img.src = data.photo;
      }
    }
    """,
)


def render_color_picker(photo_bytes: bytes, key="color_picker"):
    """Render pixel color picker. Returns hex color string or None."""
    photo_b64 = base64.b64encode(photo_bytes).decode()
    data_url = f"data:image/jpeg;base64,{photo_b64}"
    result = color_picker_component(
        data={"photo": data_url},
        default={"color": None},
        key=key,
    )
    return result.color if result and hasattr(result, "color") else None
