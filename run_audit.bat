@echo off
setlocal
cd /d "%~dp0"

set URL=%~1
set PAGES=%~2
set MODE=%~3

if "%URL%"=="" (
    echo ============================================================
    echo   InersiaLab Software Department - SEO Audit Toolkit
    echo ============================================================
    echo.
    set /p URL="Enter Website URL to Audit (e.g. https://example.com): "
)

if "%URL%"=="" (
    echo No URL provided. Launching Desktop GUI...
    if exist ".venv\Scripts\pythonw.exe" (
        start "" ".venv\Scripts\pythonw.exe" gui.py
    ) else if exist ".venv\Scripts\python.exe" (
        start "" ".venv\Scripts\python.exe" gui.py
    ) else (
        start "" python gui.py
    )
    exit /b
)

if "%PAGES%"=="" (
    echo.
    echo Crawl Scope: 0 = Unlimited (All Pages)
    set /p PAGES="Enter number of pages [Default: 0]: "
)
if "%PAGES%"=="" set PAGES=0

if "%MODE%"=="" (
    echo.
    echo Report Modes: short (recommended, ~17 pages), detailed, both
    set /p MODE="Enter report mode [Default: short]: "
)
if "%MODE%"=="" set MODE=short

echo.
echo Starting audit on %URL% (Scope: %PAGES%, Mode: %MODE%)...
echo ============================================================
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" agy_seo.py audit "%URL%" --max-pages %PAGES% --mode %MODE%
) else (
    python agy_seo.py audit "%URL%" --max-pages %PAGES% --mode %MODE%
)

echo.
pause
