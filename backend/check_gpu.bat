@echo off
chcp 65001 >nul
title GPU tekshiruv
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe check_gpu.py
) else (
    py check_gpu.py
)
echo.
pause
