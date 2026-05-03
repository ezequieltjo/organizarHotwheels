# Hot Wheels Organizer - Design Spec

Ferramenta para organizar coleção de Hot Wheels em expositores usando critérios visuais.

## Stack

- **Streamlit** — interface web
- **SQLite** — persistência local (sqlite3 built-in)
- **Pandas** — manipulação de dados + importação CSV/Excel
- **Pillow** — processamento de fotos
- **Matplotlib ou Plotly** — renderização do grid visual

## Arquitetura

```
organizarHotwheels/
├── app.py                  # Entry point Streamlit
├── models.py               # Dataclasses: Car, Shelf, ShelfConfig
├── storage.py              # CRUD com SQLite
├── organizers.py           # Algoritmos de organização
├── visualizer.py           # Geração do grid visual
├── importer.py             # Importação CSV/Excel
├── db/
│   └── collection.db       # Banco SQLite (auto-criado)
├── photos/                 # Fotos dos carros
└── requirements.txt
```

Fluxo: Cadastro → Seleção de modo → Algoritmo calcula posições → Grid visual + lista exportável.

## Modelo de Dados

### Carro
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | int (auto) | Identificador |
| modelo | str | Nome do modelo |
| marca | str | Fabricante |
| ano | int | Ano de fabricação |
| cor | str | Nome da cor |
| cor_hex | str | Código hexadecimal (#RRGGBB) |
| serie_tipo | str | Série (Mainline, Premium, Treasure Hunt, etc.) |
| favorito | bool | Destaque visual |
| foto_path | str | Caminho da foto |
| expositor_id | int (nullable) | Expositor onde está posicionado |
| posicao_linha | int (nullable) | Linha no expositor |
| posicao_coluna | int (nullable) | Coluna no expositor |

### ShelfConfig
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | int (auto) | Identificador |
| nome | str | Nome do expositor |
| linhas | int | Quantidade de linhas |
| colunas | int | Quantidade de colunas |

## Algoritmos de Organização

Posições são geradas como mapeamento temporário `{carro_id: (expositor_id, linha, coluna)}`. Só persiste quando o usuário clica "Aplicar".

Preenchimento: esgota expositor 1, depois 2, etc. Se carros > vagas totais, exibe aviso.

| Modo | Lógica |
|------|--------|
| Arco-íris | Converte cor → HSL, ordena por hue (0-360), preenche grid sequencial |
| Degradê | Agrupa cores por similaridade (distância euclidiana RGB), ordena grupos adjacentes |
| Por marca | Agrupa por marca, sub-ordena por cor dentro de cada grupo |
| Por ano | Ordena cronologicamente, preenche sequencial |
| Aleatório | `random.shuffle`, distribui sequencialmente |
| Favoritos na frente | Favoritos primeiro (posição 0,0), restante pelo critério escolhido |

## Interface Streamlit

### Sidebar
- Configuração de expositores (adicionar/editar/remover, definir linhas/colunas)
- Importar CSV/Excel

### Página principal — 3 abas

1. **Coleção** — lista de carros com busca/filtro, botão adicionar, upload de foto, marcar favorito
2. **Organizar** — dropdown com modo de organização, botão "Gerar", mostra grid visual colorido + lista de posições, botão "Exportar" (imagem ou CSV), botão "Aplicar" (salva posições nos carros)
3. **Expositores** — mostra estado atual de cada expositor com os carros posicionados

## Importação

CSV/Excel esperado com colunas: `modelo, marca, ano, cor, serie_tipo`. Colunas ausentes são ignoradas. Cor pode ser nome ("vermelho") ou hex ("#FF0000"). Mapeamento de nomes de cores para hex é feito internamente com dicionário pré-definido.
