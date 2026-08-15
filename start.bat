@echo off
REM ============================================================
REM   SERGAK AI — One-click start (Windows)
REM ============================================================

cd /D "%~dp0backend"

REM First-time setup: create venv if not exists
if not exist "venv\Scripts\activate.bat" (
    echo [Sergak AI] Creating virtual environment...
    py -m venv venv
    if errorlevel 1 (
        echo [ERROR] Python not found. Install Python from python.org
        pause
        exit /b 1
    )
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install deps if first run
if not exist "venv\.deps_installed" (
    echo [Sergak AI] Installing dependencies...
    pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] pip install failed.
        pause
        exit /b 1
    )
    type nul > venv\.deps_installed
)

REM Copy .env if missing
if not exist ".env" copy .env.example .env > nul

REM Start server
echo.
echo ============================================================
echo  Starting Sergak AI...
echo  Open in browser: http://localhost:5000
echo  Press Ctrl+C to stop
echo ============================================================
echo.

py -m app.main

pause
