@echo off
chcp 65001 >nul
title Kaggle API sozlash va yuklash
cd /d "%~dp0"

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   Kaggle API tokenni avtomatik sozlash va yuklash
echo ================================================================
echo.

REM 1. .kaggle papkasini yaratish
set "KAGGLE_DIR=%USERPROFILE%\.kaggle"
if not exist "%KAGGLE_DIR%" (
    mkdir "%KAGGLE_DIR%"
    echo [+] Papka yaratildi: %KAGGLE_DIR%
) else (
    echo [+] Papka mavjud: %KAGGLE_DIR%
)

REM 2. Tokenni yozish (yangi format)
echo KGAT_eef384f933b3db84c596506bf9aedee1> "%KAGGLE_DIR%\access_token"
echo [+] Token yozildi: %KAGGLE_DIR%\access_token

REM 3. Environment variable o'rnatish (bu sessiyada)
set "KAGGLE_API_TOKEN=KGAT_eef384f933b3db84c596506bf9aedee1"
echo [+] Environment variable o'rnatildi
echo.

REM 4. kaggle paketini o'rnatish
echo Kaggle paketi o'rnatilmoqda...
%PYCMD% -m pip install --upgrade kaggle --quiet

REM 5. Sinov - tokenni tekshirish
echo.
echo Token sinovi...
%PYCMD% -c "import os; os.environ['KAGGLE_API_TOKEN']='KGAT_eef384f933b3db84c596506bf9aedee1'; from kaggle import api; api.authenticate(); print('[OK] Kaggle authentication muvaffaqiyatli'); print('[OK] User:', api.config_values.get('username','-'))"

if errorlevel 1 (
    echo.
    echo [X] Kaggle bilan ulanib bo'lmadi. Token noto'g'ri bo'lishi mumkin.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo  HOZIR DATASETLAR YUKLANYAPTI - 30 daqiqacha kuting...
echo ================================================================
echo.

%PYCMD% scripts\download_kaggle.py

echo.
echo ================================================================
echo   TUGADI
echo ================================================================
pause
