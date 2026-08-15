@echo off
chcp 65001 >nul
title SH17 ni qo'shish + YAKUNIY merge (10 ta dataset)
cd /d "%~dp0"

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   BOSQICH 1/2: SH17 ni YOLO formatga konvertatsiya
echo   - 17 klassdan faqat helmet va head (IoU filter bilan)
echo   - 8,099 ta rasm tahlil qilinadi
echo ================================================================
%PYCMD% scripts\prepare_sh17.py
if errorlevel 1 (
    echo.
    echo [X] BOSQICH 1 da xatolik!
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   BOSQICH 2/2: 10 ta datasetni birlashtirish
echo   Eski 9 ta + SH17 = jami 10 dataset
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
pause
