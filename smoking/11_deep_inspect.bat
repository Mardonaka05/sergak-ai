@echo off
chcp 65001 >nul
title Sigaret datasetlarni CHUQUR TAHLIL (namunalar bilan)
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   Sigaret datasetlarni CHUQUR TAHLIL
echo ================================================================
echo.
echo   Bu skript har bir dataset uchun:
echo     1. Strukturasini chuqur tekshiradi
echo     2. Klasslarni ko'rsatadi
echo     3. Verdict beradi (USE / CHECK / SKIP)
echo     4. 5 ta NAMUNA RASM ni samples\ ga ko'chiradi
echo.
echo   Keyin Explorer'da samples papkasini ko'rib chiqasiz.
echo.

%PYCMD% scripts\deep_inspect.py

echo.
echo ================================================================
echo   Namunalarni ko'rish uchun:
echo ================================================================
echo.
if exist "E:\sergak_smoking\samples" (
    echo   explorer "E:\sergak_smoking\samples"
    start "" explorer "E:\sergak_smoking\samples"
)
echo.
pause
