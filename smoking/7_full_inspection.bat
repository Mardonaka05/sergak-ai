@echo off
chcp 65001 >nul
title Sigaret datasetlar - TO'LIQ TAHLIL
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   Sigaret datasetlar - TO'LIQ TAHLIL
echo ================================================================
echo.
echo   Bu skript har bir datasetingiz uchun:
echo     - Klasslarni ko'rsatadi
echo     - Maqsadini aniqlaydi (smoking person / cigarette / smoke)
echo     - Tavsiya beradi (USE / TRANSFORM / SKIP)
echo     - Universal class mapping rejasini ko'rsatadi
echo.

%PYCMD% scripts\full_inspection.py

echo.
echo ================================================================
echo   TAHLIL TUGADI
echo ================================================================
echo.
pause
