@echo off
title InersiaLab SEO Audit - Web Dashboard
setlocal
cd /d "C:\Users\EL ASSLI HI TECH\Downloads\agy-seo"

echo ============================================================
echo   Starting InersiaLab SEO Audit Web Server...
echo   Dashboard URL: http://127.0.0.1:8765
echo ============================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" web_ui.py
) else (
    python web_ui.py
)

pause
