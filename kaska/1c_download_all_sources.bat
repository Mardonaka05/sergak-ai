@echo off
chcp 65001 >nul
title Barcha manbalardan datasetlar
cd /d "%~dp0"

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   BARCHA MANBALARDAN datasetlarni yuklash:
echo   1. GitHub (login kerak emas)
echo   2. Kaggle (1 daqiqalik API sozlash kerak)
echo   3. HuggingFace (login kerak emas)
echo ================================================================
echo.
echo Avval kerakli paketlarni o'rnatamiz...
%PYCMD% -m pip install kaggle datasets pillow huggingface_hub --quiet

echo.
echo ================================================================
echo BOSQICH 1/3 - GitHub
echo ================================================================
%PYCMD% scripts\download_github.py

echo.
echo ================================================================
echo BOSQICH 2/3 - HuggingFace
echo ================================================================
%PYCMD% scripts\download_huggingface.py

echo.
echo ================================================================
echo BOSQICH 3/3 - Kaggle (API token tekshiruvi)
echo ================================================================
%PYCMD% scripts\download_kaggle.py

echo.
echo ================================================================
echo   YAKUN
echo ================================================================
echo.
echo Endi barcha datasetlarni birlashtirish:
echo   2_merge_datasets.bat ga ikki marta bosing
echo.
pause
