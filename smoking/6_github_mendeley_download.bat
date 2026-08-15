@echo off
chcp 65001 >nul
title GitHub + Mendeley + Zenodo - SIGARET datasetlarni yuklab olish
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
    set "PIPCMD=..\kaska\venv\Scripts\pip.exe"
) else (
    set "PYCMD=py"
    set "PIPCMD=py -m pip"
)

echo ================================================================
echo   GitHub + Mendeley + Zenodo SIGARET datasetlar
echo ================================================================
echo.
echo   Manzil:    E:\sergak_smoking\datasets\
echo.
echo   Manbalar:
echo     1. Mendeley Data  - 3 ta dataset (~5,000 rasm)
echo     2. Zenodo         - 1 ta dataset (~5,000 rasm)
echo     3. GitHub         - 8 ta repo (~2,500 rasm)
echo.
echo   Kutilgan qo'shimcha: ~12,500 rasm
echo   Mavjud:             25,300 rasm
echo   YAKUN:              ~37,800 rasm
echo.

REM E:\ disk
if exist "E:\" (
    if not exist "E:\sergak_smoking" mkdir "E:\sergak_smoking"
    if not exist "E:\sergak_smoking\datasets" mkdir "E:\sergak_smoking\datasets"
    echo [+] E:\sergak_smoking\ tayyor
) else (
    echo [!] E:\ disk topilmadi - D:\ ga saqlanadi
)

echo.
echo [+] Paketlar...
%PIPCMD% install -q --disable-pip-version-check requests tqdm

echo.
echo ================================================================
echo   Yuklab olish boshlandi (10-30 daqiqa)
echo ================================================================
echo.

%PYCMD% scripts\github_mendeley_download.py

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
