# Camera + Pixel Color Picker Design

## Summary

Add webcam capture and pixel-based color selection to the car add/edit form. Users photograph the car via camera, then click a pixel on the photo to define the car's color.

## User Flow

1. In add/edit form, button "Tirar Foto" (outside `st.form`) alongside existing file uploader
2. Click opens modal with live camera feed
3. "Capturar" freezes frame. "Refazer" returns to live feed
4. After capture, crosshair appears on frozen photo. Mouse moves crosshair
5. Click pixel -> color preview (swatch + hex). "Confirmar Cor" button
6. Modal closes. Photo saved to `photos/`. `cor_hex` field auto-filled
7. Native `st.color_picker` kept as manual fallback

## Architecture

### New file: `camera_component.py`

Dedicated Streamlit component using `streamlit.components.v1.html` with bidirectional communication.

**HTML/JS content:**
- `<video>` element with `getUserMedia` for live camera
- Canvas for frame capture and crosshair overlay
- Crosshair: SVG circle + crosshair lines, follows mouse via `mousemove`
- On click: `getImageData(x, y, 1, 1)` extracts pixel color
- Preview: color swatch rectangle + hex text
- "Confirmar" calls `Streamlit.setComponentValue({photo: base64_jpeg, color: "#RRGGBB"})`
- CSS: modal overlay, centered camera, dark backdrop

**Python wrapper:**
```python
def camera_component(key="camera"):
    import streamlit.components.v1 as components
    value = components.html(HTML_JS, height=500, key=key)
    return value  # dict with photo (base64) and color (hex) or None
```

### Integration in `app.py`

**State variables:**
- `st.session_state.camera_open: bool` - modal visibility flag
- `st.session_state.captured_photo_path: str | None` - saved photo path
- `st.session_state.captured_color: str | None` - hex color from pixel picker

**Flow:**
1. "Tirar Foto" button (outside form) sets `camera_open = True`, triggers `st.rerun()`
2. If `camera_open`: render `camera_component()` outside form
3. On component return value: decode base64 -> bytes, save to `photos/{modelo}_{timestamp}.jpg`, set session state
4. Set `camera_open = False`, rerun
5. Form reads `captured_photo_path` and `captured_color` from session state
6. After form submit: clear captured state variables

**Form layout changes:**
- Photo section: "Tirar Foto" button + `file_uploader` side by side
- If car has existing photo: show thumbnail + "Tirar Nova Foto" + upload
- Color: if `captured_color` exists, auto-fill `color_picker` with value
- `color_picker` always editable as manual override

**Edit mode:** Same UI. Existing photo shown as thumbnail. "Tirar Nova Foto" replaces it.

### Photo Storage

- Format: JPEG (quality 0.9)
- Path: `photos/{modelo}_{timestamp}.jpg`
- Base64 decoded from component -> `Path.write_bytes()`

## Files Changed

| File | Change |
|------|--------|
| `camera_component.py` | NEW - component with HTML/JS modal |
| `app.py` | Camera button, component integration, state management |

## Error Handling

- Camera permission denied: show message in modal, "Fechar" button
- No camera available: show message, suggest file upload
- Browser incompatibility: graceful fallback to file uploader

## Testing

- Manual: test camera capture, crosshair, pixel pick, form integration
- Verify photo saved to disk
- Verify color applied to car record
- Test edit existing car (replace photo + color)
- Test without camera (fallback to upload)
