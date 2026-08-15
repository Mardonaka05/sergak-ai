@echo off
chcp 65001 >nul
title Sigaret datasetlarni tahlil qilish
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   1-Qadam: Sigaret datasetlarini TAHLIL QILISH
echo ================================================================
echo.

%PYCMD% scripts\inspect_smoking.py

echo.
pause
