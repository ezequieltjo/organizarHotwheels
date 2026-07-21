@echo off
cd /d "%~dp0"

REM Define o interpretador Python (py launcher ou python)
set "PYTHON=python"
where py >nul 2>nul && set "PYTHON=py -3"

REM Cria venv se nao existir
if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual (.venv)...
    %PYTHON% -m venv .venv
    if errorlevel 1 (
        echo Erro: falha ao criar venv. Instale o Python em https://python.org
        pause
        exit /b 1
    )
)

REM Instala dependencias na primeira execucao
if not exist ".venv\Scripts\streamlit.exe" (
    echo Instalando dependencias...
    .venv\Scripts\python.exe -m pip install --upgrade pip >nul
    .venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo Erro ao instalar dependencias.
        pause
        exit /b 1
    )
)

.venv\Scripts\streamlit.exe run app.py
pause
