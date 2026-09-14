@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" gui.py
) else if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" gui.py
) else (
    start "" python gui.py
)
