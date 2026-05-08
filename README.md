# Organizar Miniaturas

App para organizar coleção de miniaturas de carros em expositores.

## Funcionalidades

- Cadastro de carros (modelo, marca do carro, fabricante da miniatura, cor, série, foto)
- Seletor gráfico de cor
- Importação via CSV/Excel
- 7 algoritmos de organização (arco-íris, gradiente, marca, fabricante, ano, aleatório, favoritos)
- Grid visual interativo com Plotly
- Exportação de posições em CSV

## Como usar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Ou clique duas vezes em `rodar.bat`.

## Estrutura

- `app.py` — Interface Streamlit
- `models.py` — Dataclasses (Car, ShelfConfig)
- `storage.py` — SQLite CRUD
- `organizers.py` — Algoritmos de organização
- `visualizer.py` — Grid Plotly
- `color_utils.py` — Utilitários de cor
- `importer.py` — Importação CSV/Excel
