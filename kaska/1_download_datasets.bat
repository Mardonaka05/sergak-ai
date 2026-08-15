@echo off
chcp 65001 >nul
title Roboflow datasetlarini yuklash
cd /d "%~dp0"

echo ================================================================
echo   Roboflow datasetlarini yuklash
echo ================================================================
echo.
echo   1. Avval scripts\download_roboflow_datasets.py faylini oching
echo   2. PRIVATE_API_KEY ni o'z Private kalitingiz bilan almashtiring
echo   3. Faylni saqlang
echo   4. Bu skriptni qayta ishga tushiring
echo.
pause

REM Roboflow paketi o'rnatilganmi tekshirish
if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo.
echo Roboflow paketi tekshirilmoqda...
%PYCMD% -m pip install roboflow

echo.
echo Datasetlarni yuklash boshlanmoqda...
%PYCMD% scripts\download_roboflow_datasets.py

echo.
pause
