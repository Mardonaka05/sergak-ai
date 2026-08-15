@echo off
chcp 65001 >nul
title Sergak AI - Kamera va Modul sozlash
cd /d "%~dp0"

echo ================================================================
echo   Sergak AI - Kameralar va modullarni avtomatik sozlash
echo ================================================================
echo.
echo  Bu skript quyidagilarni bajaradi:
echo    1. .pt fayllarni models_pt/ ga ko'chiradi
echo    2. 4 ta Hikvision kamerani qo'shadi (NVR: 192.168.5.10)
echo    3. AI modullarni .pt fayllar bilan bog'laydi
echo.
echo  Tekshiring:
echo    - Backend hozir TO'XTATILGAN bo'lishi kerak
echo    - OpenServer (MariaDB) ishlamoqda
echo    - Kamera quvvati yoqilgan (192.168.5.10 ga ping ishlasin)
echo.
pause

echo.
echo Python topilmoqda...

if exist "venv\Scripts\python.exe" (
    set "PYCMD=venv\Scripts\python.exe"
    echo Venv Python ishlatamiz
    goto :run
)

py -V >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=py"
    goto :run
)

echo [!] Python topilmadi
pause
exit /b 1

:run
echo Python: %PYCMD%
echo.

%PYCMD% setup_cameras_and_modules.py

echo.
echo ================================================================
if errorlevel 1 (
    echo [!] Sozlash XATO bilan tugadi
) else (
    echo [OK] Sozlash tugadi
    echo.
    echo Endi backendni qayta ishga tushiring:
    echo   2_start_backend.bat ga ikki marta bosing
)
echo ================================================================
pause
