@echo off
chcp 65001 >nul
title Qo'shimcha datasetlarni yuklash
cd /d "%~dp0"

echo ================================================================
echo   Qo'shimcha helmet datasetlarni Roboflow Universe'dan yuklash
echo ================================================================
echo.
echo   15 ta nomzodni sinab koramiz.
echo   Maqsad: 5-10 ta yangi dataset muvaffaqiyatli yuklash.
echo.
echo   Vaqt: 10-30 daqiqa (internet tezligiga qarab)
echo.
pause

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo.
%PYCMD% scripts\download_more_datasets.py

echo.
pause
