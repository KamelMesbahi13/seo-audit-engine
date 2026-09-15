@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    if exist ".venv\Scripts\pythonw.exe" (
        start "" ".venv\Scripts\pythonw.exe" gui.py
        exit /b
    ) else if exist ".venv\Scripts\python.exe" (
        start "" ".venv\Scripts\python.exe" gui.py
        exit /b
    ) else (
        start "" python gui.py
        exit /b
    )
) else (
    set PAGES=%~2
    if "%PAGES%"=="" set PAGES=0
    if exist ".venv\Scripts\python.exe" (
        ".venv\Scripts\python.exe" agy_seo.py audit "%~1" --max-pages %PAGES%
    ) else (
        python agy_seo.py audit "%~1" --max-pages %PAGES%
    )
    pause
)
