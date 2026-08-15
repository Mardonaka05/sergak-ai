@echo off
chcp 65001 >nul
title YANGI 3 dataset + YAKUNIY merge (9 ta dataset)
cd /d "%~dp0"

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   BOSQICH 1/2: 3 ta YANGI datasetni VOC-^>YOLO konversiya
echo   SHEL5K     (5,000 rasm)
echo   GDUT-HWD   (3,174 rasm, 5 ta rangli kaska)
echo   SHWD       (7,581 rasm — eng katta)
echo ================================================================
%PYCMD% scripts\prepare_more_datasets.py
if errorlevel 1 (
    echo.
    echo [X] BOSQICH 1 da xatolik!
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   BOSQICH 2/2: YAKUNIY merge - 9 ta datasetni birlashtirish
echo   Eski 6 ta + yangi 3 ta = jami 9 dataset
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
echo   Natija:  D:\sergak dasturi\kaska\merged
echo   YAML:    D:\sergak dasturi\kaska\merged\data.yaml
echo.
echo   Kutilgan natija (taxminan):
echo     - 55,000+ rasm
echo     - 400,000+ bbox
echo.
pause
