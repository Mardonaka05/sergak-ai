@echo off
chcp 65001 >nul
title Yangi datasetlarni tayyorlash va birlashtirish
cd /d "%~dp0"

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   BOSQICH 1/2: Yangi datasetlarni tayyorlash
echo   (data.yaml yaratish + VOC->YOLO konversiya)
echo ================================================================
%PYCMD% scripts\prepare_new_datasets.py

echo.
echo ================================================================
echo   BOSQICH 2/2: Hammasini birlashtirish (avtomatik aniqlash)
echo ================================================================
%PYCMD% scripts\merge_datasets.py

echo.
pause
