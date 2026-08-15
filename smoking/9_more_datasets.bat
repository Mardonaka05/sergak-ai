@echo off
chcp 65001 >nul
title YANGI Sigaret Datasetlar - images.cv + Open Images + boshqalar
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
    set "PIPCMD=..\kaska\venv\Scripts\pip.exe"
) else (
    set "PYCMD=py"
    set "PIPCMD=py -m pip"
)

echo ================================================================
echo   YANGI SIGARET DATASETLAR YUKLAB OLISH
echo ================================================================
echo.
echo   Manzil: E:\sergak_smoking\datasets\
echo.
echo   Yangi manbalar:
echo     1. images.cv         - 3 ta dataset (10,300 rasm)
echo     2. Smoke100k         - qo'lda link beriladi
echo     3. GitHub Releases   - 2 ta dataset
echo     4. Open Images V7    - 5,000 Cigarette rasm (Google)
echo.

REM E:\ disk
if exist "E:\" (
    if not exist "E:\sergak_smoking" mkdir "E:\sergak_smoking"
    if not exist "E:\sergak_smoking\datasets" mkdir "E:\sergak_smoking\datasets"
    echo [+] E:\sergak_smoking\ tayyor
)

echo.
echo [+] Paketlarni o'rnatish...
%PIPCMD% install -q --disable-pip-version-check fiftyone requests tqdm rarfile

echo.
echo ================================================================
echo   YUKLAB OLISH BOSHLANDI
echo   Vaqt: 30-60 daqiqa
echo ================================================================
echo.

%PYCMD% scripts\more_datasets.py

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
