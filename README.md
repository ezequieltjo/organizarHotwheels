# Organizar Miniaturas

App para organizar coleção de miniaturas de carros em expositores.

## Funcionalidades

- Cadastro de carros (modelo, marca do carro, fabricante da miniatura, cor, série, foto)
- Seletor gráfico de cor
- Importação via CSV/Excel
- 7 algoritmos de organização (arco-íris, gradiente, marca, fabricante, ano, aleatório, favoritos)
- Grid visual interativo com Plotly
- Exportação de posições em CSV

## Pré-requisitos

- **Python 3.10+** (testado com 3.13).

## Como rodar localmente

### Windows

1. Instale o Python em <https://python.org> (marque **Add Python to PATH**).
2. Abra o terminal na pasta do projeto.
3. Instale as dependências:
   ```cmd
   pip install -r requirements.txt
   ```
4. Rode o app de um dos modos:
   - Dê dois cliques em `rodar.bat`, **ou**
   - No terminal:
     ```cmd
     streamlit run app.py
     ```

### Linux

> Em distros como Arch/CachyOS o `pip` global é bloqueado (PEP 668).
> Use um ambiente virtual — é o caminho recomendado e funciona em qualquer distro.

1. Instale o Python pelo gerenciador de pacotes (Debian/Ubuntu: `sudo apt install python3 python3-venv`; Arch/CachyOS: já vem no sistema).
2. Crie e ative um venv:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Rode o app de um dos modos:
   - Pelo script (usa o `.venv` automaticamente se existir):
     ```bash
     ./rodar.sh
     ```
   - Ou direto no terminal (com o venv ativado):
     ```bash
     streamlit run app.py
     ```

O app abre em <http://localhost:8501> (ou porta indicada no terminal).

## Estrutura

- `app.py` — Interface Streamlit
- `models.py` — Dataclasses (Car, ShelfConfig)
- `storage.py` — SQLite CRUD
- `organizers.py` — Algoritmos de organização
- `visualizer.py` — Grid Plotly
- `color_utils.py` — Utilitários de cor
- `importer.py` — Importação CSV/Excel
