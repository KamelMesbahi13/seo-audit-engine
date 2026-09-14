@echo off
setlocal enabledelayedexpansion

set "SKILL_DIR=%~dp0"
set "PYTHON_EXE=%SKILL_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Error: Python environment not found at %PYTHON_EXE%
    exit /b 1
)

"%PYTHON_EXE%" "%SKILL_DIR%agy_seo.py" %*
