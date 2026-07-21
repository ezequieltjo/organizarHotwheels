#!/bin/sh
cd "$(dirname "$0")" || exit 1

PYTHON="${PYTHON:-python3}"

# Cria venv se não existir
if [ ! -x ".venv/bin/python" ]; then
    echo "Criando ambiente virtual (.venv)..."
    "$PYTHON" -m venv .venv || { echo "Erro: falha ao criar venv. Verifique 'python3-venv'."; exit 1; }
fi

# Instala dependências na primeira execução
if [ ! -x ".venv/bin/streamlit" ]; then
    echo "Instalando dependências..."
    .venv/bin/pip install --upgrade pip >/dev/null
    .venv/bin/pip install -r requirements.txt || { echo "Erro ao instalar dependências."; exit 1; }
fi

.venv/bin/streamlit run app.py
