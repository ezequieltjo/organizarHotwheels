# Redesign da Interface Streamlit — organizarHotwheels

**Data:** 2026-10-22
**Branch:** `ui-redesign` (a partir de `master`)
**Status:** aprovado pelo usuário

## Contexto

O app é um catalogador de Hot Wheels em Streamlit (`app.py`, 1275 linhas), com 7 abas no topo, toolbar de filtros com 5 selects visíveis, cards de carro com botões-emoji e muito CSS ad-hoc injetado via `st.markdown`/`st.html`. Deploy-alvo inclui Streamlit Community Cloud (repo público). Branches recentes mostram evolução orgânica por patches; a interface acumulou hacks (`setInterval` para estilizar botões, sniffing de User-Agent, seletores `:has()` frágeis).

## Objetivo

Interface que permita uso **rápido e simples**: navegação por sidebar, cards limpos e consistentes, toolbar compacta, tema próprio com a identidade do app (vermelho `#ea1c2c`, amarelo `#f9d908` da logo). Manter Streamlit e compatibilidade total com a Community Cloud.

## Não objetivos

- Trocar de framework (React etc.) — fica para a decisão futura de "substituir".
- Mudar lógica de dados: `storage.py`, `organizers.py`, `models.py`, `importer.py`, `backup.py`, `thumbs.py` intocados.
- Mudar comportamento funcional existente (filtros, organizadores, backup, zoom, mobile).

## Restrições

- **Cloud:** apenas deps já em `requirements.txt` (todas wheel); nada de filesystem local fora do padrão atual. Filesystem da Community Cloud é efêmero — coleção online = a commitada no repo; gravação permanece no desktop. Documentar no spec, não no app.
- **Streamlit 1.59.1** (pin atual): `st.navigation`, `st.Page`, `st.popover`, `st.pills`, ícones `:material/...`, `st.toast` disponíveis. Tema dark duplo: verificar suporte real na implementação; não prometer.
- **Dados no git:** `db/collection.db` e `photos/` commitados. Convenção: mudanças de coleção commitam na `master`; mudanças de UI, na branch. Sem trocar de branch com dados pendentes.

## Design

### 1. Estrutura de código

```
app.py              # entry point: st.navigation + render da página ativa
ui/theme.py         # constantes de cor (logo), injeção de CSS central
ui/cards.py         # card do carro — componente único (coleção e desejos)
ui/filters.py       # toolbar de busca/filtro/ordem reutilizável
views/colecao.py    # aba Coleção (lista + form adicionar/editar)
views/desejos.py    # Lista de Desejos (grid de cards)
views/estatisticas.py
views/expositores.py
views/organizar.py
views/backup.py
views/ajuda.py
```

`app.py` vira entry fino. Cada view é função de render; estado e callbacks existentes migram junto com sua view. Split inicial é mecânico, sem mudança de comportamento (commit separado).

### 2. Navegação

- `st.navigation` com páginas: Coleção, Desejos, Estatísticas, Expositores, Organizar, Backup, Como Usar — ícones `:material/...` + labels.
- Logo no topo da sidebar; header nativo do Streamlit oculto (como hoje).
- Run automático por página (Streamlit multipage), eliminando custo de render das 6 outras abas por interação — ganho direto de velocidade.

### 3. Tema

- `.streamlit/config.toml`: `primaryColor #ea1c2c`, fundo neutro claro (fotos ganham contraste), fonte própria suportada pela versão.
- CSS ad-hoc dos hacks atuais (`setInterval`, seletores frágeis) substituído por classes próprias e tema nativo.
- Dark mode: só se 1.59 suportar tema duplo limpo; caso contrário, fica de fora (documentado).

### 4. Card do carro (`ui/cards.py`)

- Foto 4:3 com borda na cor do carro (ou swatch da cor, sem foto) — comportamento atual mantido.
- Nome do carro; marcadores ★ favorito, 📦 arquivado, 🖌️ customizado, 🔁 repetido viram pills pequenas e discretas (não prefixo de texto).
- Ações com ícones `:material/...` em `st.button`/`st.popover` (favoritar, arquivar, editar, excluir), tamanho consistente — mata o JS de `markButtons`.
- Zoom: `st.dialog` atual mantido; overlay invisível sobre a foto continua.

### 5. Toolbar (`ui/filters.py`)

- Busca sempre visível ( campo único, como hoje).
- Filtros marca/série/fabricante/status dentro de `st.popover` com contador de filtros ativos no label.
- Ordenação: select inline; status curto via `st.pills` se couber melhor.
- Reset ↺ mantém comportamento (limpa tudo).
- Contador "N exibidos" mantido.

### 6. Detalhes

- Toast custom em JS → `st.toast` nativo (sucesso verde, remoção com estilo próprio se nativo não diferenciar).
- Empty states: `st.info`/ilustração leve nas listas vazias.
- Mobile: manter funcionamento atual (grade 2 col, zoom por toque); CSS responsivo substitui sniffing de UA onde possível, sem regressão.

### 7. Verificação

- App rodando local (`streamlit run app.py`) após cada commit da branch.
- Screenshots de cada página, desktop + viewport mobile, via playwright-cli; comparação visual com a master.
- `pytest` (testes de dados/lógica) verde — nada de lógica mudou.

## Ordem de implementação (commits na branch)

1. Branch `ui-redesign` + `.streamlit/config.toml` (tema base)
2. Split de `app.py` em módulos, sem mudança de comportamento
3. Navegação sidebar (`st.navigation`)
4. Componente de card
5. Toolbar compacta
6. Detalhes (toast, pills, empty states, limpeza de CSS morto)
7. Passada de screenshots + ajustes finos

## Decisão final

Merge de `ui-redesign` em `master` (ou descarte) é decisão do usuário após comparar as duas versões rodando lado a lado.
