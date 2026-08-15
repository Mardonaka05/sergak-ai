@echo off
chcp 65001 >nul
title Datasetlarni birlashtirish (2 klass)
cd /d "%~dp0"

echo ================================================================
echo   Datasetlarni 2 klassga birlashtirish
echo   (helmet, no_helmet)
echo ================================================================
echo.
echo   Manba:
echo     1. roboflow_joseph_hardhat  (7,035 rasm)
echo     2. roboflow_ppe             (11,978 rasm)
echo     3. helmet-tracking-2        (3,837 rasm)
echo.
echo   Natija: D:\sergak dasturi\kaska\merged\
echo.
pause

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo.
%PYCMD% scripts\merge_datasets.py

echo.
echo ================================================================
echo   Tugadi
echo ================================================================
pause
