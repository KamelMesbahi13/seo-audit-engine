@echo off
title InersiaLab SEO Audit Engine - Terminal
setlocal
cd /d C:\Users\EL ASSLI HI TECH\Downloads\agy-seo

set URL=%~1
set PAGES=%~2
set MODE=%~3

echo ============================================================
echo   InersiaLab Software Department - SEO Audit Engine
echo ============================================================
echo.

if %URL%==" (
 set /p URL=Enter Website URL to Audit [Default: https://inersialab.com]: 
)
if %URL%== set URL=https://inersialab.com

if %PAGES%== (
 echo.
 echo Crawl Scope:
 echo 0 = Unlimited (Crawls ALL pages of the website)
 echo Or enter a specific number (e.g. 10, 50)
 set /p PAGES=Enter crawl scope [Default: 0]: 
)
if %PAGES%== set PAGES=0

if %MODE%== (
 echo.
 echo Report Modes:
 echo 1. short (Recommended - Consolidated summary of defects & fixes)
 echo 2. detailed (Full exhaustive report with all problems & fixes)
 echo 3. both (Generates both short and detailed reports)
 set /p MODE=Enter report mode [1, 2, or 3 - Default: 1]: 
)
if %MODE%== set MODE=short
if %MODE%==1 set MODE=short
if %MODE%==2 set MODE=detailed
if %MODE%==3 set MODE=both

echo.
echo ============================================================
echo Target URL : %URL%
echo Crawl Scope : %PAGES% (0 = Unlimited All Pages)
echo Report Mode : %MODE%
echo ============================================================
echo.

if exist .venv\Scripts\python.exe (
 .venv\Scripts\python.exe agy_seo.py audit %URL% --max-pages %PAGES% --mode %MODE%
) else (
 python agy_seo.py audit %URL% --max-pages %PAGES% --mode %MODE%
)

echo.
echo ============================================================
echo Audit finished. Check your Downloads folder for the PDF.
echo Press any key to exit...
echo ============================================================
pause >nul
