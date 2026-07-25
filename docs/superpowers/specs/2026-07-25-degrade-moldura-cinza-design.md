# Degradê Moldura de Cinza — Design

**Data:** 2026-07-25
**Status:** Aprovado
**Modo afetado:** "Degradê (similaridade)" → "Degradê (moldura)"

## Resumo

Trocar a lógica do modo de organização **Degradê** para que os carros da escala de cinza formem uma **moldura (anel/perímetro)** ao redor dos carros coloridos. O gradiente cinza percorre o anel no sentido horário, do **preto** ao **branco**, com o ponto de encontro (seam) no centro da linha de topo. A classificação de "cinza" passa a ser um único limiar de **% de saturação HSV**, exposto como um slider para o usuário ajustar e re-rodar a alocação até encontrar o limiar ideal.

## Contexto

O modo atual (`_gradient_2d_fill` em `organizers.py`) divide os cinzas em duas colunas laterais (claro à esquerda, escuro à direita) e coloca os cromáticos no miolo por `hue→coluna` + `value→linha`. A classificação `_is_gray()` usa 4 regras HSV fixas. O usuário quer uma moldura visual de cinza envolvendo os coloridos, com controle interativo do limiar de saturação.

## Requisitos

### Funcionais

1. Cinzas formam o **perímetro** da grade (anel externo), coloridos ficam no **miolo**.
2. Gradiente cinza: **preto → branco**, sentido **horário**.
3. **Seam no centro do topo**: preto começa em `(linha0, cols//2)` (centro-direita do topo); branco termina em `(linha0, cols//2 - 1)` (centro-esquerda), adjacente ao preto.
4. Caminho horário: topo direita → desce borda direita → fundo esquerda → sobe borda esquerda → topo esquerda.
5. Classificação de cinza = **único limiar de saturação HSV**: cor é cinza se `saturação <= limiar%`. Substitui as 4 regras atuais. Preto/branco/cinza-neutro (sat ≈ 0) sempre contam como cinza.
6. **3 controles de configuração** (apenas no modo Degradê):
   - Slider **Saturação máx p/ cinza (%)** — intervalo 0–50, default 12.
   - Seletor **Anel parcial** — como tratar casas vagas do perímetro quando há poucos cinzas.
   - Seletor **Miolo colorido** — como organizar coloridos dentro da moldura.
7. **Auto re-rodar**: ao mexer em qualquer controle, se já existe uma organização gerada no modo Degradê, a alocação é regenerada automaticamente antes de renderizar.
8. Cinzas em excesso (mais que o perímetro) viram **anel interno concêntrico**, continuando o gradiente.

### Estratégias de "Anel parcial"

Quando o número de cinzas é menor que o perímetro:

| Estratégia | Comportamento |
|---|---|
| **Colorido preenche** (default) | Cinzas preenchem o anel horário (preto→branco) até acabar. Casas vagas do perímetro recebem coloridos excedentes. Nenhum carro fica de fora enquanto houver slot. |
| **Vagas vazias** | Perímetro reservado só para cinzas. Casas vagas ficam vazias. Coloridos só no miolo. Pode deixar carros sem vaga se o miolo encher. |
| **Estica gradiente** | Cinzas distribuídos uniformemente pelo anel inteiro (preto→branco espaçados a cada `P/N` posições, onde P = perímetro, N = cinzas). Anel sempre completo visualmente. |

### Estratégias de "Miolo colorido"

| Estratégia | Comportamento |
|---|---|
| **Hue+value** (default) | `hue→coluna` (arco-íris esq→dir) + `value→linha` (topo claro, baixo escuro). Reaproveita lógica atual. |
| **Similaridade** | Vizinho mais próximo por `distancia_rgb` (reusa `_nearest_neighbor_sort`). Agrupa tons parecidos lado a lado. |

## Arquitetura

### Abordagem escolhida: A — `GradientConfig` dataclass imutável

Dataclass `frozen=True` agrupa os 3 parâmetros. Threaded apenas em `organize_gradient`. Lógica do anel extraída em helpers dedicados para manter funções < 50 linhas. Não polui a assinatura uniforme do dict `ORGANIZERS` em `app.py`.

Alternativas consideradas: parâmetros soltos na assinatura (B) — inflado, quebra padrão; módulo separado `gradient_ring.py` (C) — isolamento melhor mas refactor prematuro enquanto `organizers.py` cabe no limite.

## Componentes

### 1. `GradientConfig` (novo, em `models.py`)

```python
@dataclass(frozen=True)
class GradientConfig:
    sat_threshold_pct: float = 12.0       # intervalo 0-50
    partial_strategy: str = "colorido"    # colorido | vazio | estica
    interior_strategy: str = "hue_value"  # hue_value | similaridade
```

Imutável (regra de imutabilidade do projeto). Default permite chamar `organize_gradient` sem config.

### 2. `_is_gray(hex_color, sat_threshold)` — refatoração

Substitui a versão de 4 regras. Única regra:

```python
def _is_gray(hex_color: str, sat_threshold: float) -> bool:
    _, s, _ = _hex_to_hsv(hex_color)
    return s <= sat_threshold
```

`sat_threshold` em escala 0–1 (converter `% / 100` no caller). Preto/branco/cinza-neutro têm `s ≈ 0` → sempre cinza.

### 3. `_ring_fill` — algoritmo do anel (novo, em `organizers.py`)

Reusa `_build_slot_list` para obter slots globais `(global_row, global_col)` e o mapeamento `slot_map` para coordenadas reais de expositor.

Passos:

1. Classifica cada carro em cinza vs colorido via `_is_gray(cor_hex, sat_threshold)`.
2. Gera a **ordem do anel** — lista de células do perímetro em sentido horário começando em `(0, cols//2)`:
   - `(0, cols//2)` → `(0, cols-1)` (topo, direita)
   - `(1, cols-1)` → `(rows-1, cols-1)` (borda direita, baixo)
   - `(rows-1, cols-2)` → `(rows-1, 0)` (fundo, esquerda)
   - `(rows-2, 0)` → `(1, 0)` (borda esquerda, cima)
   - `(0, cols//2 - 1)` (topo esquerda até o seam)
3. Ordena cinzas por `value` (mais escuro primeiro = preto).
4. Atribui cinzas às posições do anel na ordem. Se cinzas > perímetro, continua no **anel interno concêntrico** (sub-grade com offset `(1,1)`, `rows-2 × cols-2`, mesma ordem horária), repetindo até esgotar.
5. Aplica **estratégia parcial** (se cinzas < perímetro):
   - `colorido`: deixa buracos; preenchidos depois por coloridos excedentes.
   - `vazio`: deixa buracos vazios.
   - `estica`: redistribui cinzas uniformemente pelo anel (`step = max(1, P // N)`, cinza `i` na posição `i * step`).
6. Coloca coloridos no **miolo** (células internas, i.e., não-perímetro) conforme `interior_strategy`.
7. Coloridos excedentes do miolo → preenchem buracos do anel (se `partial=colorido`) → qualquer slot vazio restante (via `_find_nearest_real_slot`).
8. Mapeia grade resultante → slots reais via `slot_map` + `_find_nearest_real_slot` (reuso).

### 4. `organize_gradient` — assinatura estendida

```python
def organize_gradient(cars, shelves, wall=None, disabled=None,
                      config: GradientConfig | None = None) -> dict:
    cars = _filter_reserva(cars)
    if not cars:
        return {}
    cfg = config or GradientConfig()
    return _ring_fill(cars, shelves, wall, disabled, cfg)
```

### 5. `app.py` — aba Organizar

- Renomear entrada do dict `ORGANIZERS`: `"Degradê (similaridade)"` → `"Degradê (moldura)"`.
- Quando `modo` selecionado contém "Degradê", renderizar 3 controles abaixo do seletor, valores em `st.session_state`:
  - `st.slider("Saturação máx p/ cinza (%)", 0, 50, 12, key="deg_sat")`
  - `st.selectbox("Anel parcial", ["Colorido preenche", "Vagas vazias", "Estica gradiente"], key="deg_partial")`
  - `st.selectbox("Miolo colorido", ["Hue+value", "Similaridade"], key="deg_interior")`
- Construir `GradientConfig` a partir dos valores.
- **Auto re-rodar**: no início da lógica de renderização do tab3, se `"assignment" in st.session_state` e modo é Degradê → regenerar `assignment` com a config atual (antes de `st.plotly_chart`).
- Botão "Gerar organização" permanece para 1ª geração e demais modos. Ao clicar em modo Degradê, usa a config atual.
- Passar config só em `organize_gradient`; demais organizadores chamam sem config.

## Tratamento de erros / casos extremos

- **Sem cinzas:** sem moldura; anel vira buracos tratados pela estratégia parcial (default: colorido preenche). Miolo recebe todos os coloridos.
- **Sem coloridos:** só anel; miolo vazio.
- **Threshold = 0%:** só neutros puros (preto/branco/cinza) viram moldura; cores levemente dessaturadas viram miolo.
- **Threshold = 50%:** captura cores pouco saturadas (rosa-pálido, bege, cinza-azulado).
- **Mais carros que slots:** aviso já existente em `app.py` mantido.
- **Slots desabilitados (`disabled`):** `_build_slot_list` já filtra; anel percorre só células válidas.
- **Parede multi-expositor (`wall`):** `_build_slot_list` já trata grade global; anel opera sobre a grade global consolidada.

## Testes (pytest, padrão AAA)

Em `tests/test_organizers.py`:

- `test_is_gray_pure_saturation`: cor saturada (vermelho puro) = colorida; cinza neutro = cinza; marrom-escuro saturado = colorido (diferença chave vs regra antiga que o classificava como cinza); preto/branco = cinza.
- `test_ring_starts_black_at_seam`: primeiro cinza (mais escuro) cai em `(0, cols//2)`; último (mais claro) adjacente em `(0, cols//2 - 1)`.
- `test_ring_clockwise_order`: células do anel seguem ordem horária a partir do seam.
- `test_concentric_inner_ring`: cinzas excedentes ao perímetro aparecem no anel interno.
- `test_partial_colorido_fills_gaps`: buracos do anel recebem coloridos.
- `test_partial_vazio_leaves_empty`: buracos do anel ficam sem carro.
- `test_partial_estica_distributes`: cinzas espaçados uniformemente pelo anel.
- `test_interior_hue_value`: coloridos no miolo por hue→col / value→linha.
- `test_interior_similaridade`: coloridos agrupados por similaridade RGB.
- `test_no_grays`: apenas coloridos, sem moldura.
- `test_no_colored`: apenas anel.
- `test_respects_disabled_slots`: slots bloqueados não recebem carros.

Cobertura alvo: ≥ 80% no código novo/modificado.

## Fora de escopo (YAGNI)

- Persistir `GradientConfig` no banco (fica só em `session_state`; re-aplicar posições salva o assignment final, não a config).
- Animar a transição do anel.
- Migrar os outros modos (arco-íris, marca, etc.) para a estrutura de config.

## Plano de implementação

Definido na etapa seguinte via skill `writing-plans`.
