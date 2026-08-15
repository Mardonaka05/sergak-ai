@echo off
chcp 65001 >nul
title Sigaret Datasetlarni Tekshirish
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   Sigaret Datasetlarni Tekshirish
echo ================================================================
echo.

%PYCMD% scripts\check_datasets.py

echo.
pause
