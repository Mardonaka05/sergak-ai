@echo off
chcp 65001 >nul
title YAKUNIY merge - barcha 6 ta datasetni birlashtirish
cd /d "%~dp0"

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   BOSQICH 1/2: Yangi datasetlarni tayyorlash
echo   (data.yaml yaratish + VOC-^>YOLO konversiya)
echo ================================================================
%PYCMD% scripts\prepare_new_datasets.py
if errorlevel 1 (
    echo.
    echo [X] BOSQICH 1 da xatolik!
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   BOSQICH 2/2: YAKUNIY merge (final_merge.py - EXPLICIT 6 dataset)
echo   A-stil: joseph_hardhat, ppe, helmet_tracking, construction_safety
echo   B-stil: andrewmvd_yolo, yolo_helmethead
echo ================================================================
%PYCMD% scripts\final_merge.py
if errorlevel 1 (
    echo.
    echo [X] BOSQICH 2 da xatolik!
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   BARCHASI MUVAFFAQIYATLI TUGADI
echo ================================================================
echo   Natija: D:\sergak dasturi\kaska\merged
echo   data.yaml: D:\sergak dasturi\kaska\merged\data.yaml
echo.
pause
