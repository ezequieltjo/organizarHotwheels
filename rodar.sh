#!/bin/sh
cd "$(dirname "$0")" || exit 1
if [ -x ".venv/bin/streamlit" ]; then
    .venv/bin/streamlit run app.py
else
    streamlit run app.py
fi
