# UI Redesign (Streamlit) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesenhar a interface Streamlit do organizarHotwheels (navegação em sidebar, tema próprio, cards e toolbar redesenhados) mantendo lógica de dados intocada e compatibilidade com Streamlit Community Cloud.

**Architecture:** `app.py` (1275 linhas) divide-se em módulos `ui/` (tema, fotos, cards, filtros, estado) e `views/` (uma por página). `app.py` vira entry fino com `st.navigation`. Código de dados (`storage`, `organizers`, `models`, `importer`, `backup`, `thumbs`) não muda.

**Tech Stack:** Streamlit 1.59.1, Python 3, Plotly, pytest (suite de dados existente).

## Global Constraints

- Branch de trabalho: `ui-redesign` (criada a partir de `master` em 9219a37).
- Lógica de dados intocada: nada em `storage.py`, `organizers.py`, `models.py`, `importer.py`, `backup.py`, `thumbs.py`, `color_utils.py`, `color_sliders.py`, `visualizer.py`, `camera_component.py`.
- Suite de testes sempre verde: `.venv/Scripts/python.exe -m pytest tests/ -q` (baseline: 180 passed).
- Deps: só as já em `requirements.txt` (streamlit, pandas, openpyxl, pillow, plotly). Nenhuma dependência nova.
- Compatível com Streamlit Community Cloud: filesystem usado apenas em `photos/` e `db/` (padrão atual), nada de caminhos absolutos.
- Verificação visual de cada task: rodar o app (`.venv/Scripts/python.exe -m streamlit run app.py --server.headless true --server.port 8501`) e screenshotar com playwright-cli.
- Commits pequenos, um por task, terminando com `Co-Authored-By: Claude Code <noreply@anthropic.com>`.
- Mudanças de coleção (db/fotos geradas por uso manual) NÃO devem ser commitadas nesta branch.

---

### Task 1: Tema base (`.streamlit/config.toml`)

**Files:**
- Create: `.streamlit/config.toml`

**Interfaces:**
- Consumes: nada.
- Produces: tema claro com primaryColor `#ea1c2c` usado por todos os widgets nativos; decisão documentada sobre tema dark duplo.

- [ ] **Step 1: Criar config.toml com tema claro**

```toml
[theme]
base = "light"
primaryColor = "#ea1c2c"
backgroundColor = "#faf9f7"
secondaryBackgroundColor = "#f0ede8"
textColor = "#201d1a"
```

Não definir `font` customizada ainda — testar separadamente no Step 3.

- [ ] **Step 2: Rodar app e verificar tema**

Run: `.venv/Scripts/python.exe -m streamlit run app.py --server.headless true --server.port 8501` (em background), screenshot com playwright-cli.

Expected: botões primários vermelhos `#ea1c2c`, fundo off-white, sem erros no console.

- [ ] **Step 3: Investigar fonte customizada e tema dark (Streamlit 1.59)**

Consultar docs do Streamlit (context7) para 1.59: (a) `theme.font` com nomes de Google Fonts e seção `theme.fontFaces`; (b) temas duplos light/dark em config.toml. Se suportado sem gambiarra, adicionar variante dark harmônica (fundo `#17151a`, surface `#211e24`, primary igual). Se não, registrar decisão: "dark fica de fora" (spec prevê isso).

- [ ] **Step 4: Screenshot de confirmação + Commit**

```bash
git add .streamlit/config.toml
git commit -m "feat(ui): tema claro com identidade do app em config.toml

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 2: Split mecânico de `app.py` em módulos (comportamento idêntico)

Refactor puro: nenhuma mudança visual nem de comportamento. Tabs continuam; só o código se move. Renomeações removem underscore de nomes públicos.

**Files:**
- Create: `ui/__init__.py`, `ui/state.py`, `ui/photos.py`, `ui/theme.py`, `ui/filters.py`, `ui/cards.py`
- Create: `views/__init__.py`, `views/colecao.py`, `views/desejos.py`, `views/estatisticas.py`, `views/expositores.py`, `views/organizar.py`, `views/backup.py`, `views/ajuda.py`
- Rewrite: `app.py`

**Interfaces:**
- Produces (consumidos pelas Tasks 3–6):
  - `ui.state.refresh() -> None`
  - `ui.photos.PHOTOS_DIR: Path`, `ui.photos.THUMBS_DIR: Path`, `ui.photos.resolve_photo(path: str) -> Path | None`, `ui.photos.img_b64(path) -> str`, `ui.photos.img_thumb_b64(path) -> str`, `ui.photos.save_photo(photo_bytes: bytes, modelo: str, old_path: str | None = None) -> str`, `ui.photos.remove_photo(path: str | None) -> None`
  - `ui.theme.LOGO_VERMELHO`, `ui.theme.LOGO_AMARELO`, `ui.theme.LARANJA: str`, `ui.theme.inject_base_css() -> None`, `ui.theme.render_logo() -> None`
  - `ui.filters.STATUS_FILTRO_OPTS: list[str]`, `ui.filters.nomes_repetidos(cars: list) -> set`, `ui.filters.filter_cars(cars, busca, marca, serie, status="Todos", fabricante="Todos") -> list`, `ui.filters.reset_filtros(prefix: str) -> None`, `ui.filters.ORDEM_OPTS: list[str]`, `ui.filters.sort_cars(cars: list, ordem: str) -> list`, `ui.filters.list_toolbar(source: list, prefix: str) -> list`
  - `ui.cards.is_mobile() -> bool`, `ui.cards.foto_html(car) -> str`, `ui.cards.act_zoom(car) -> None`, `ui.cards.zoom_dialog(car) -> None`, `ui.cards.maybe_zoom() -> None`, `ui.cards.zoom_btn(car, prefix: str) -> None`, `ui.cards.render_car_card(car, repetidos, prefix, actions) -> None`, `ui.cards.render_car_list(source, prefix, actions) -> None`
  - `views.colecao.COLECAO_ACTIONS: list`, `views.colecao.render() -> None`; cada `views/*.render()`

- [ ] **Step 1: Criar `ui/` com o código movido**

Tabela de movimentação (código verbatim de `app.py`, só renomeando):

| app.py (linhas) | destino | nome novo |
|---|---|---|
| 28–30 (`PHOTOS_DIR`, `THUMBS_DIR`) | `ui/photos.py` | `PHOTOS_DIR`, `THUMBS_DIR` (paths via `Path(__file__).parent.parent / "photos"`) |
| 60–80 `_resolve_photo` | `ui/photos.py` | `resolve_photo` |
| 83–88 `_img_b64` | `ui/photos.py` | `img_b64` |
| 91–96 `_img_thumb_b64` | `ui/photos.py` | `img_thumb_b64` |
| 154–166 `_save_photo` | `ui/photos.py` | `save_photo` |
| 169–181 `_remove_photo` | `ui/photos.py` | `remove_photo` |
| 32–35 cores | `ui/theme.py` | `LOGO_VERMELHO`, `LOGO_AMARELO`, `LARANJA` |
| 50–54 `refresh` | `ui/state.py` | `refresh` |
| 184–233 (STATUS/`_nomes_repetidos`/`_filter_cars`/`_reset_filtros`/ORDEM/`_ordenar`) | `ui/filters.py` | `STATUS_FILTRO_OPTS`, `nomes_repetidos`, `filter_cars`, `reset_filtros`, `ORDEM_OPTS`, `sort_cars` |
| 338–373 `_list_toolbar` | `ui/filters.py` | `list_toolbar` |
| 376–379 `_is_mobile` | `ui/cards.py` | `is_mobile` |
| 99–108 `_foto_html` | `ui/cards.py` | `foto_html` |
| 111–151 (`_act_zoom`/`_zoom_dialog`/`_maybe_zoom`/`_zoom_btn`) | `ui/cards.py` | `act_zoom`, `zoom_dialog`, `maybe_zoom`, `zoom_btn` |
| 382–439 (`_render_car_card`/`_render_car_list`) | `ui/cards.py` | `render_car_card`, `render_car_list` |
| 442–452 bloco logo | `ui/theme.py` | `render_logo()` (mesma HTML/base64) |
| 463–500 CSS (`_HW_PAIR_SEL` + `<style>`) | `ui/theme.py` | `inject_base_css()` (chamada por `app.py`) |

`inject_base_css()` contém o CSS existente verbatim (tabs font-size, number input +/-, `_HW_PAIR_SEL`, overlay de zoom, thumb 60x45). `render_logo()` mantém `LOGO_HEADER_HEIGHT = "9rem"`.

**ui/cards.py — ajuste de imports** (exemplo, demais seguem o padrão):

```python
import streamlit as st
from ui.photos import resolve_photo, img_thumb_b64
from ui.filters import nomes_repetidos, list_toolbar


def is_mobile() -> bool:
    """True em celular (User-Agent com 'Mobi'). iPad não tem 'Mobi'."""
    ua = st.context.headers.get("User-Agent") or ""
    return "Mobi" in ua
```

- [ ] **Step 2: Criar `views/` movendo o corpo das tabs para funções `render()`**

| app.py (linhas) | destino | conteúdo |
|---|---|---|
| 257–306 (`_act_*` + `COLECAO_ACTIONS`) + 502–760 (tab1) | `views/colecao.py` | callbacks `act_favorito`, `act_reserva`, `act_editar`, `act_excluir`, `act_promover`, `COLECAO_ACTIONS`, `render()` |
| 308–335 (`_wish_card`/`_wish_grid`) + 762–768 (tab_wish) | `views/desejos.py` | `wish_card`, `wish_grid`, `render()` |
| 770–867 (tab2) | `views/expositores.py` | `render()` |
| 869–995 (tab3) + 454–457 (`_export_cached`) | `views/organizar.py`, `views/backup.py` | `render()` em cada; `export_cached` vai para backup.py |
| 997–1057 (tab4) | `views/estatisticas.py` | `render()` (cores via `from ui.theme import LOGO_VERMELHO, LOGO_AMARELO, LARANJA`) |
| 1078–1119 (tab_backup) | `views/backup.py` | `render()` |
| 1121–1245 (tab_ajuda) | `views/ajuda.py` | `render()` |

Imports que as views carregam do app atual migram junto (`models`, `storage`, `organizers`, `importer`, `ui.*`). `views/colecao.py` importa `ui.state.refresh` etc. Toast JS (1060–1076) fica em `app.py` por ora.

- [ ] **Step 3: Reescrever `app.py` como orquestrador (tabs intactos)**

```python
import streamlit as st
st.set_page_config(layout="wide")
from storage import init_db
from ui.state import refresh
from ui.theme import inject_base_css, render_logo
from views import (colecao, desejos, estatisticas, expositores,
                   organizar, backup, ajuda)

init_db()
if "cars" not in st.session_state:
    refresh()

inject_base_css()
render_logo()

tab1, tab_wish, tab4, tab2, tab3, tab_backup, tab_ajuda = st.tabs(
    ["Coleção", "Lista de Desejos", "Estatísticas", "Expositores", "Organizar", "Backup", "❓ Como Usar"])
with tab1: colecao.render()
with tab_wish: desejos.render()
with tab4: estatisticas.render()
with tab2: expositores.render()
with tab3: organizar.render()
with tab_backup: backup.render()
with tab_ajuda: ajuda.render()

# bloco st.html final (toast JS) permanece aqui, verbatim do app.py atual
```

- [ ] **Step 4: Testes e app**

Run: `.venv/Scripts/python.exe -m pytest tests/ -q` — Expected: 180 passed.
Run: app em background + screenshots de todas as abas — Expected: visual idêntico à master.

- [ ] **Step 5: Commit**

```bash
git add app.py ui/ views/
git commit -m "refactor(ui): divide app.py em ui/ e views/ sem mudança de comportamento

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 3: Navegação sidebar (`st.navigation`)

**Files:**
- Modify: `app.py`

**Interfaces:**
- Consumes: `views/*.render()` (Task 2).
- Produces: navegação em sidebar; views rodam isoladas por página (só a ativa executa).

- [ ] **Step 1: Trocar tabs por `st.navigation` (páginas por callable)**

```python
import streamlit as st
st.set_page_config(layout="wide", page_title="organizarHotwheels",
                   page_icon=":material/directions_car:")
from storage import init_db
from ui.state import refresh
from ui.theme import inject_base_css, render_logo
from views import (colecao, desejos, estatisticas, expositores,
                   organizar, backup, ajuda)

init_db()
if "cars" not in st.session_state:
    refresh()

pg = st.navigation([
    st.Page(colecao.render, title="Coleção", icon=":material/directions_car:", default=True),
    st.Page(desejos.render, title="Lista de Desejos", icon=":material/favorite"),
    st.Page(estatisticas.render, title="Estatísticas", icon=":material/leaderboard"),
    st.Page(expositores.render, title="Expositores", icon=":material/shelves"),
    st.Page(organizar.render, title="Organizar", icon=":material/auto_awesome_motion"),
    st.Page(backup.render, title="Backup", icon=":material/backup"),
    st.Page(ajuda.render, title="Como Usar", icon=":material/help"),
])

inject_base_css()
render_logo()          # agora via st.sidebar, altura ~4rem
pending_toast()        # placeholder até Task 6 (no-op) — ou manter toast JS
pg.run()
```

`render_logo()` muda para desenhar na sidebar (`st.sidebar.image` do `photos/logo.png`, `use_container_width=True`) com nome do app. Header nativo continua oculto via CSS em `inject_base_css()`.

- [ ] **Step 2: Remover CSS de tabs morto**

Em `inject_base_css()`, apagar a regra `[data-testid='stTabs'] button{font-size:1.25rem}` (tabs não existem mais). Resto permanece.

- [ ] **Step 3: Testes e app**

Run: pytest — 180 passed. App: navegar pelas 7 páginas, screenshot de cada; conferir que interações (favoritar, editar, gerar organização) continuam funcionando por página.

- [ ] **Step 4: Commit**

```bash
git add app.py ui/theme.py
git commit -m "feat(ui): navegação por sidebar com st.navigation

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 4: Card do carro (pills + ícones material)

**Files:**
- Modify: `ui/cards.py`, `ui/theme.py`, `views/colecao.py`, `views/desejos.py`, `app.py`

**Interfaces:**
- Consumes: `Car` (models), helpers de `ui.photos`.
- Produces: `ui.cards.badges_html(car, repetidos: set) -> str`; `COLECAO_ACTIONS` com ícones material; JS `markButtons`/`setInterval` removido.

- [ ] **Step 1: `badges_html` em `ui/cards.py`**

```python
def badges_html(car, repetidos: set) -> str:
    """Pills discretas: ★ favorito · arquivado · custom · repetido."""
    pills = []
    if car.favorito:
        pills.append('<span class="hw-badge hw-badge-fav" title="Favorito">★</span>')
    if car.reserva:
        pills.append('<span class="hw-badge" title="Arquivado (não posicionado)">arquivado</span>')
    if car.customizada:
        pills.append('<span class="hw-badge" title="Customizado">custom</span>')
    if car.modelo in repetidos:
        pills.append('<span class="hw-badge" title="Modelo repetido na coleção">repetido</span>')
    return "".join(pills)
```

- [ ] **Step 2: CSS das pills em `ui/theme.py` (dentro de `inject_base_css`)**

```css
.hw-badge{display:inline-block;font-size:.62rem;font-weight:600;letter-spacing:.03em;
  text-transform:uppercase;padding:.1rem .45rem;border-radius:99px;
  background:rgba(0,0,0,.08);color:inherit;vertical-align:middle;margin-left:.25rem}
.hw-badge-fav{background:#f9d908;color:#3a3000}
```

- [ ] **Step 3: Ações com ícones material em `views/colecao.py`**

```python
COLECAO_ACTIONS = [
    (lambda c: ":material/star" if c.favorito else ":material/star_border",
     "Favoritar/desfavoritar", act_favorito),
    (lambda c: ":material/inventory_2" if c.reserva else ":material/inventory",
     "Arquivar/desarquivar (não posiciona)", act_reserva),
    (lambda c: ":material/edit", "Editar", act_editar),
    (lambda c: ":material/delete", "Excluir", act_excluir),
]
```

Substituir o prefixo textual de marcadores (`★ `/`📦 `/`🖌️ `/`🔁 `) em `render_car_card` e na linha desktop por `badges_html(car, repetidos)` ao lado do nome. Nos desejos (`views/desejos.py`), trocar ➕/🗑️ por `:material/add_circle` e `:material/delete`.

**Verificação de API:** `st.button(":material/star")` renderiza ícone no 1.59. Screenshot confirma; se aparecer texto literal `:material/...`, voltar para emoji (fallback documentado, sem bloquear a task).

- [ ] **Step 4: Remover JS `markButtons`/`setInterval` de `app.py`**

No bloco `st.html` final, apagar a função `markButtons`, o `setInterval` e as regras `.car-actions-row` (CSS já não faz nada — os botões nativos com ícones substituem o estilo forçado). Toast JS permanece até Task 6.

- [ ] **Step 5: Testes e app**

Run: pytest — 180 passed. App: screenshots Coleção (desktop + mobile) e Desejos; conferir pills, ícones, zoom clicando na foto, favoritar/arquivar/editar/excluir funcionando.

- [ ] **Step 6: Commit**

```bash
git add ui/cards.py ui/theme.py views/colecao.py views/desejos.py app.py
git commit -m "feat(ui): cards com pills de marcadores e ícones material; remove JS de botões

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 5: Toolbar compacta (popover de filtros)

**Files:**
- Modify: `ui/filters.py`

**Interfaces:**
- Consumes: `filter_cars`, `sort_cars`, `reset_filtros`, `ORDEM_OPTS`, `STATUS_FILTRO_OPTS`.
- Produces: `ui.filters.list_toolbar(source: list, prefix: str) -> list` (mesma assinatura — chamadores não mudam).

- [ ] **Step 1: Redesenhar `list_toolbar`**

Busca + ordenação + reset + contador fora; os 4 filtros dentro de um `st.popover` com contador de ativos. Status via `st.pills` (seleção única) dentro do popover.

```python
def _ativos(source, prefix) -> int:
    defaults = {"filtro_marca": "Todas", "filtro_serie": "Todas",
                "filtro_fabricante": "Todos", "filtro_status": "Todos"}
    return sum(1 for k, d in defaults.items()
               if st.session_state.get(f"{k}_{prefix}", d) != d)


def _um(sel):
    """st.pills single pode devolver str ou list — normaliza."""
    if isinstance(sel, list):
        return sel[0] if sel else "Todos"
    return sel or "Todos"


def list_toolbar(source: list, prefix: str) -> list:
    n_exibidos = len(filter_cars(source, st.session_state.get(f"busca_{prefix}", "")))
    sb, mid, cnt = st.columns([4, 1.2, 1])
    with sb:
        busca = st.text_input("Buscar", placeholder="modelo, marca, fabricante ou série…",
                              key=f"busca_{prefix}", label_visibility="collapsed")
    with mid:
        st.markdown("<div style='height:.35rem'></div>", unsafe_allow_html=True)
        n = _ativos(source, prefix)
        rotulo = f":material/tune: Filtros ({n})" if n else ":material/tune: Filtros"
        with st.popover(rotulo, use_container_width=True):
            filtro_marca = st.selectbox("Marca", ["Todas"] + sorted(set(c.marca for c in source if c.marca)), key=f"filtro_marca_{prefix}")
            filtro_serie = st.selectbox("Série", ["Todas"] + sorted(set(c.serie_tipo for c in source if c.serie_tipo)), key=f"filtro_serie_{prefix}")
            filtro_fabricante = st.selectbox("Fabricante", ["Todos"] + sorted(set(c.fabricante for c in source if c.fabricante)), key=f"filtro_fabricante_{prefix}")
            filtro_status = _um(st.pills("Status", STATUS_FILTRO_OPTS,
                                         key=f"filtro_status_{prefix}",
                                         selection_mode="single"))
    with cnt:
        st.markdown("<div style='height:.35rem'></div>", unsafe_allow_html=True)
        cc1, cc2 = st.columns([1, 1.4], gap="small")
        with cc1:
            st.button("↺", help="Limpar busca e filtros", key=f"reset_filtros_{prefix}",
                      on_click=reset_filtros, args=(prefix,))
        with cc2:
            st.markdown(f"<div style='margin-top:.4rem;font-size:1.05rem'><b>{n_exibidos}</b> exibidos</div>",
                        unsafe_allow_html=True)
    ordem = st.selectbox("Ordenar por", ORDEM_OPTS, key=f"ordem_{prefix}",
                         label_visibility="collapsed")
    return sort_cars(filter_cars(source, busca, filtro_marca, filtro_serie,
                                 filtro_status, filtro_fabricante), ordem)
```

Nota: `reset_filtros` também precisa limpar o novo formato de `filtro_status_` (aceita list ou str — reuso do `_um` ou setar `"Todos"`).

- [ ] **Step 2: Testes e app**

Run: pytest — 180 passed. App: Coleção e Desejos — filtrar por marca dentro do popover, contador sobe, busca filtra, reset limpa tudo, "N exibidos" correto.

- [ ] **Step 3: Commit**

```bash
git add ui/filters.py
git commit -m "feat(ui): toolbar compacta com filtros em popover e pills de status

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 6: Detalhes (toast nativo, empty states, limpeza CSS)

**Files:**
- Modify: `ui/state.py`, `views/colecao.py`, `views/desejos.py`, `views/expositores.py`, `views/organizar.py`, `app.py`, `ui/theme.py`

**Interfaces:**
- Consumes: `st.toast`.
- Produces: `ui.state.pending_toast() -> None` (chamada no topo de `app.py`); toast JS removido.

- [ ] **Step 1: Toast nativo em `ui/state.py`**

```python
def notify(text: str, icon: str = "✅") -> None:
    """Agenda toast nativo para o próximo run (sobrevive ao st.rerun)."""
    st.session_state._hw_toast = {"text": text, "icon": icon}


def pending_toast() -> None:
    msg = st.session_state.pop("_hw_toast", None)
    if msg:
        st.toast(msg["text"], icon=msg["icon"])
```

Trocar nos callbacks (`_car_toast_msg`/`car_toast`) por `notify("Carro adicionado com sucesso!")`, `notify("Carro removido!", icon="🗑️")` etc. Em `app.py`, chamar `pending_toast()` antes de `pg.run()` e apagar o bloco JS de toast + `_toast_*` (1060–1076).

- [ ] **Step 2: Empty states consistentes**

Listas vazias usam `st.info` com ícone material: coleção vazia `:material/car_crash` "Nenhum carro na coleção. Adicione pelo formulário." — desejos `:material/favorite` — estatísticas mantêm as mensagens atuais com ícone. (Coleção/Desejos/Estatísticas.)

- [ ] **Step 3: Limpeza de CSS morto em `ui/theme.py`**

Remover seletores sem efeito após o redesign (`stFormSubmitButton` nowrap mantém; `car-actions-row` já foi; revisar `stTabs` restos). Manter: overlay de zoom, `_HW_PAIR_SEL` (mobile), number input +/-. Layout da organização (overflow-x do plotly) permanece em `views/organizar.py`.

- [ ] **Step 4: Testes e app**

Run: pytest — 180 passed. App: adicionar/excluir carro (toast aparece e some), páginas vazias mostram empty state, nenhum erro de console.

- [ ] **Step 5: Commit**

```bash
git add app.py ui/state.py ui/theme.py views/
git commit -m "feat(ui): toast nativo, empty states e limpeza de CSS

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 7: Screenshots finais + ajustes finos

**Files:**
- Modify: os que os ajustes exigirem (descoberta visual).

**Interfaces:**
- Consumes: tudo das Tasks 1–6.
- Produces: branch pronta para decisão de merge.

- [ ] **Step 1: Matriz de screenshots**

Playwright-cli: 7 páginas × (desktop 1440×900, mobile 390×844). Fluxos: adicionar carro, editar, favoritar, zoom, gerar organização, exportar backup.

- [ ] **Step 2: Corrigir o que a matriz revelar** (alinhamentos, espaçamentos, contraste). Um commit por correção coesa.

- [ ] **Step 3: Verificação final**

pytest 180 passed; app sobe limpo; sem CSS/JS morto; deploy-cloud mental check (só deps do requirements, paths relativos).

- [ ] **Step 4: Push da branch**

```bash
git push -u origin ui-redesign
```

Decisão de merge fica com o usuário (comparar master × ui-redesign rodando as duas).
