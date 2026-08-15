@echo off
chcp 65001 >nul
title ULTIMATE Sigaret Datasetlar - 100% ishlaydigan manbalardan
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
    set "PIPCMD=..\kaska\venv\Scripts\pip.exe"
) else (
    set "PYCMD=py"
    set "PIPCMD=py -m pip"
)

echo ================================================================
echo   ULTIMATE Sigaret Datasetlar Yuklab Olish
echo ================================================================
echo.
echo   Manzil:   E:\sergak_smoking\datasets\
echo.
echo   Faqat 100%% ISHLAYDIGAN manbalar:
echo     1. Open Images V7 (Google) - 10,000+ rasm
echo     2. Mendeley Data           - 3 ta dataset
echo     3. Zenodo                  - 1 ta dataset
echo     4. HuggingFace             - 1 ta dataset
echo     5. GitHub                  - 8 ta repo
echo.
echo   Skip:
echo     - Roboflow (CDN blokirovka)
echo     - Kaggle (ToS muammosi)
echo.

REM E:\ disk
if exist "E:\" (
    if not exist "E:\sergak_smoking" mkdir "E:\sergak_smoking"
    if not exist "E:\sergak_smoking\datasets" mkdir "E:\sergak_smoking\datasets"
    echo [+] E:\sergak_smoking\ tayyor
)

echo.
echo [+] Kerakli paketlarni o'rnatish...
%PIPCMD% install -q --disable-pip-version-check fiftyone huggingface_hub requests tqdm

echo.
echo ================================================================
echo   YUKLAB OLISH BOSHLANDI
echo   Vaqt: 30-60 daqiqa (Open Images V7 katta)
echo ================================================================
echo.

%PYCMD% scripts\ultimate_download.py

echo.
echo ================================================================
echo   TUGADI
echo ================================================================
echo.

if exist "E:\sergak_smoking\datasets" (
    echo Tekshirish: explorer "E:\sergak_smoking\datasets"
)
echo.
pause
