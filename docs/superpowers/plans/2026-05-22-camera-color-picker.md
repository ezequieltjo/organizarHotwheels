# Camera + Pixel Color Picker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add webcam photo capture and pixel-based color selection to car add/edit forms.

**Architecture:** `st.camera_input()` for native camera capture, `st.components.v2.component()` for crosshair color picker. Photo and color managed via `st.session_state`, outside Streamlit forms. Form submit reads from session_state.

**Tech Stack:** Streamlit (components v2), HTML5 Canvas, getUserMedia

**Note:** TDD not applicable for UI components. Manual testing in Task 4.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `camera_component.py` | CREATE | Color picker component definition + Python wrapper |
| `app.py` | MODIFY | Camera input, color picker integration, form restructure |

---

### Task 1: Create color picker component

**Files:**
- Create: `camera_component.py`

- [ ] **Step 1: Create `camera_component.py`**

```python
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
```

- [ ] **Step 2: Verify import works**

Run: `python -c "from camera_component import render_color_picker; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add camera_component.py
git commit -m "feat: add pixel color picker component (Streamlit v2)"
```

---

### Task 2: Restructure app.py — add camera input and color picker

**Files:**
- Modify: `app.py`

Key changes:
1. Import `render_color_picker` and `base64`
2. Move `camera_input` + `file_uploader` OUTSIDE both forms
3. Store captured photo bytes and picked color in `st.session_state`
4. Form reads photo/color from session_state on submit
5. Clear session_state after submit

- [ ] **Step 1: Add imports at top of `app.py`**

After `from color_utils import nome_para_hex` (line 14), add:

```python
from camera_component import render_color_picker
import time
```

- [ ] **Step 2: Add photo helper functions before tab definitions**

Before `tab1, tab2, tab3 = st.tabs(...)` (line 42), add:

```python
def _save_photo(photo_bytes, modelo):
    """Save photo to disk, return path."""
    ts = int(time.time() * 1000)
    safe = "".join(c if c.isalnum() else "_" for c in modelo)[:30]
    path = str(PHOTOS_DIR / f"{safe}_{ts}.jpg")
    Path(path).write_bytes(photo_bytes)
    return path
```

- [ ] **Step 3: Replace the add car form (lines 115-156)**

Replace the entire `else:` block inside `with c2:` (from `st.subheader("Adicionar carro")` through the `st.rerun()` at line 156) with:

```python
        else:
            st.subheader("Adicionar carro")
            existing_marcas = sorted(set(c.marca for c in st.session_state.cars if c.marca))
            existing_fabricantes = sorted(set(c.fabricante for c in st.session_state.cars if c.fabricante))
            existing_series = sorted(set(c.serie_tipo for c in st.session_state.cars if c.serie_tipo))

            # --- Photo capture (outside form) ---
            st.markdown("**Foto do carro**")
            pc1, pc2 = st.columns(2)
            with pc1:
                camera_photo = st.camera_input("📷 Tirar Foto", key="cam_add")
            with pc2:
                file_photo = st.file_uploader("📁 Upload", type=["jpg", "jpeg", "png"], key="upload_add")

            source = camera_photo or file_photo
            if source:
                st.session_state._pending_photo = source.getvalue()

            # --- Color picker ---
            picker_color = None
            if st.session_state.get("_pending_photo"):
                st.markdown("**Clique na foto para selecionar a cor**")
                picker_color = render_color_picker(st.session_state._pending_photo, key="picker_add")
                if picker_color:
                    st.session_state._pending_picker_color = picker_color

            # --- Form (no photo uploader) ---
            with st.form("add_car"):
                modelo = st.text_input("Modelo")
                marca_sel = st.selectbox("Marca do carro", existing_marcas + ["+ Nova marca"])
                marca_nova = st.text_input("Nova marca (preencher se '+ Nova marca')", key="marca_nova_add")
                fabricante_sel = st.selectbox("Fabricante da miniatura", existing_fabricantes + ["+ Novo fabricante"])
                fabricante_novo = st.text_input("Novo fabricante (preencher se '+ Novo fabricante')", key="fabricante_novo_add")
                serie_sel = st.selectbox("Série", existing_series + ["+ Nova série"])
                serie_nova = st.text_input("Nova série (preencher se '+ Nova série')", key="serie_nova_add")
                ano = st.number_input("Ano", min_value=1950, max_value=2030, value=2024)
                cor = st.text_input("Cor (nome ou #hex)", placeholder="deixe vazio para usar o seletor")
                default_color = st.session_state.get("_pending_picker_color") or "#808080"
                cor_picker = st.color_picker("Seletor de cor", value=default_color, key="cor_picker_add")
                if st.form_submit_button("Adicionar"):
                    marca = marca_nova.strip() if marca_sel == "+ Nova marca" and marca_nova.strip() else (marca_sel if marca_sel != "+ Nova marca" else "")
                    fabricante = fabricante_novo.strip() if fabricante_sel == "+ Novo fabricante" and fabricante_novo.strip() else (fabricante_sel if fabricante_sel != "+ Novo fabricante" else "")
                    serie = serie_nova.strip() if serie_sel == "+ Nova série" and serie_nova.strip() else (serie_sel if serie_sel != "+ Nova série" else "")
                    if modelo.strip():
                        if cor.strip():
                            cor_hex = nome_para_hex(cor.strip())
                        else:
                            cor_hex = st.session_state.get("_pending_picker_color") or cor_picker.upper()
                            cor = ""
                        foto_path = ""
                        if st.session_state.get("_pending_photo"):
                            foto_path = _save_photo(st.session_state._pending_photo, modelo.strip())
                        insert_car(Car(
                            modelo=modelo.strip(), marca=marca,
                            fabricante=fabricante, ano=ano,
                            cor=cor.strip(), cor_hex=cor_hex, serie_tipo=serie,
                            foto_path=foto_path
                        ))
                        st.session_state.pop("_pending_photo", None)
                        st.session_state.pop("_pending_picker_color", None)
                        refresh()
                        st.session_state._car_toast_msg = "Carro adicionado com sucesso!"
                        st.session_state.car_toast = True
                        st.rerun()
```

- [ ] **Step 4: Replace the edit car form (lines 57-114)**

Replace the `if editing_car:` block inside `with c2:` with:

```python
        if editing_car:
            st.subheader(f"Editar: {editing_car.modelo}")
            existing_marcas = sorted(set(c.marca for c in st.session_state.cars if c.marca))
            existing_fabricantes = sorted(set(c.fabricante for c in st.session_state.cars if c.fabricante))
            existing_series = sorted(set(c.serie_tipo for c in st.session_state.cars if c.serie_tipo))

            # --- Photo capture (outside form) ---
            st.markdown("**Foto do carro**")
            if editing_car.foto_path and Path(editing_car.foto_path).exists():
                st.image(editing_car.foto_path, width=200)
            pc1, pc2 = st.columns(2)
            with pc1:
                camera_photo = st.camera_input("📷 Tirar Foto", key="cam_edit")
            with pc2:
                file_photo = st.file_uploader("📁 Upload (substituir)", type=["jpg", "jpeg", "png"], key="upload_edit")

            source = camera_photo or file_photo
            if source:
                st.session_state._pending_photo = source.getvalue()
            elif editing_car.foto_path and Path(editing_car.foto_path).exists():
                # Load existing photo for color picker
                st.session_state.setdefault("_pending_photo", Path(editing_car.foto_path).read_bytes())

            # --- Color picker ---
            picker_color = None
            if st.session_state.get("_pending_photo"):
                st.markdown("**Clique na foto para selecionar a cor**")
                picker_color = render_color_picker(st.session_state._pending_photo, key="picker_edit")
                if picker_color:
                    st.session_state._pending_picker_color = picker_color

            # --- Form ---
            with st.form("edit_car"):
                modelo = st.text_input("Modelo", value=editing_car.modelo)
                marca_opts = existing_marcas + ["+ Nova marca"]
                marca_idx = marca_opts.index(editing_car.marca) if editing_car.marca in marca_opts else 0
                marca_sel = st.selectbox("Marca do carro", marca_opts, index=marca_idx, key="edit_marca_sel")
                marca_nova = st.text_input("Nova marca (preencher se '+ Nova marca')", key="marca_nova_edit")
                fab_opts = existing_fabricantes + ["+ Novo fabricante"]
                fab_idx = fab_opts.index(editing_car.fabricante) if editing_car.fabricante in fab_opts else 0
                fabricante_sel = st.selectbox("Fabricante da miniatura", fab_opts, index=fab_idx, key="edit_fab_sel")
                fabricante_novo = st.text_input("Novo fabricante (preencher se '+ Novo fabricante')", key="fabricante_novo_edit")
                serie_opts = existing_series + ["+ Nova série"]
                serie_idx = serie_opts.index(editing_car.serie_tipo) if editing_car.serie_tipo in serie_opts else 0
                serie_sel = st.selectbox("Série", serie_opts, index=serie_idx, key="edit_serie_sel")
                serie_nova = st.text_input("Nova série (preencher se '+ Nova série')", key="serie_nova_edit")
                ano = st.number_input("Ano", min_value=1950, max_value=2030, value=editing_car.ano)
                cor = st.text_input("Cor (nome ou #hex)", value=editing_car.cor, placeholder="deixe vazio para usar o seletor")
                default_color = st.session_state.get("_pending_picker_color") or editing_car.cor_hex or "#808080"
                cor_picker = st.color_picker("Seletor de cor", value=default_color, key="cor_picker_edit")
                bc1, bc2 = st.columns(2)
                save = bc1.form_submit_button("Salvar")
                cancel = bc2.form_submit_button("Cancelar")
                if cancel:
                    st.session_state.pop("_pending_photo", None)
                    st.session_state.pop("_pending_picker_color", None)
                    del st.session_state.editing_car_id
                    st.rerun()
                if save:
                    marca = marca_nova.strip() if marca_sel == "+ Nova marca" and marca_nova.strip() else (marca_sel if marca_sel != "+ Nova marca" else "")
                    fabricante = fabricante_novo.strip() if fabricante_sel == "+ Novo fabricante" and fabricante_novo.strip() else (fabricante_sel if fabricante_sel != "+ Novo fabricante" else "")
                    serie = serie_nova.strip() if serie_sel == "+ Nova série" and serie_nova.strip() else (serie_sel if serie_sel != "+ Nova série" else "")
                    if modelo.strip():
                        if cor.strip():
                            cor_hex = nome_para_hex(cor.strip())
                        else:
                            cor_hex = st.session_state.get("_pending_picker_color") or cor_picker.upper()
                            cor = ""
                        foto_path = editing_car.foto_path
                        if st.session_state.get("_pending_photo"):
                            foto_path = _save_photo(st.session_state._pending_photo, modelo.strip())
                        editing_car.modelo = modelo.strip()
                        editing_car.marca = marca
                        editing_car.fabricante = fabricante
                        editing_car.ano = ano
                        editing_car.cor = cor.strip()
                        editing_car.cor_hex = cor_hex
                        editing_car.serie_tipo = serie
                        editing_car.foto_path = foto_path
                        update_car(editing_car)
                        st.session_state.pop("_pending_photo", None)
                        st.session_state.pop("_pending_picker_color", None)
                        del st.session_state.editing_car_id
                        refresh()
                        st.session_state._car_toast_msg = "Carro editado com sucesso!"
                        st.session_state.car_toast = True
                        st.rerun()
```

- [ ] **Step 5: Run app to verify no import/syntax errors**

Run: `streamlit run app.py --server.headless true`
Expected: App loads without errors.

- [ ] **Step 6: Commit**

```bash
git add app.py
git commit -m "feat: camera input + pixel color picker in add/edit forms"
```

---

### Task 3: Handle edge cases and cleanup

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Clear pending state when entering edit mode**

When user clicks "Edit" on a car (line ~214), clear previous pending photo/color:

Find:
```python
                    if bc2.button("✏️", key=f"edit_{car.id}"):
                        st.session_state.editing_car_id = car.id
                        st.rerun()
```

Replace with:
```python
                    if bc2.button("✏️", key=f"edit_{car.id}"):
                        st.session_state.editing_car_id = car.id
                        st.session_state.pop("_pending_photo", None)
                        st.session_state.pop("_pending_picker_color", None)
                        st.rerun()
```

- [ ] **Step 2: Clear pending state when car is deleted**

Find:
```python
                    if bc3.button("🗑️", key=f"del_{car.id}"):
                        delete_car(car.id)
```

Replace with:
```python
                    if bc3.button("🗑️", key=f"del_{car.id}"):
                        st.session_state.pop("_pending_photo", None)
                        st.session_state.pop("_pending_picker_color", None)
                        delete_car(car.id)
```

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "fix: clear pending photo/color state on edit/delete actions"
```

---

### Task 4: Manual testing

- [ ] **Step 1: Start the app**

Run: `streamlit run app.py`

- [ ] **Step 2: Test add car with camera**
1. Click "Tirar Foto" in add car section
2. Take a photo
3. Color picker should appear below
4. Move mouse over photo — crosshair follows, preview shows color
5. Click a pixel — "Confirmar Cor" button appears
6. Click "Confirmar Cor" — color fills the color picker field
7. Fill remaining fields, submit — car added with photo and color

- [ ] **Step 3: Test add car with file upload**
1. Upload a photo via file uploader
2. Same color picker flow
3. Submit — car added with uploaded photo

- [ ] **Step 4: Test edit existing car**
1. Click edit on a car
2. Existing photo shown
3. Color picker shows on existing photo
4. Pick new color, submit — color updated

- [ ] **Step 5: Test edit car without photo**
1. Edit a car that has no photo
2. Upload or take photo
3. Pick color, submit — photo and color saved

- [ ] **Step 6: Test cancel edit**
1. Edit a car, take photo
2. Cancel — photo discarded, no state leak

- [ ] **Step 7: Test fallback color picker**
1. Add car without photo
2. Use native `st.color_picker` manually
3. Submit — color from manual picker used
