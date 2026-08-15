@echo off
chcp 65001 >nul
title Sergak AI - SQLite -> MySQL Migratsiya
cd /d "%~dp0"

echo ================================================================
echo   Sergak AI - SQLite to MySQL migratsiyasi
echo ================================================================
echo.
echo  Manba:    %CD%\sergak.db
echo  Maqsad:   mysql://root@localhost:3306/sergak_ai
echo.
echo  Avval tekshiring:
echo    1. OpenServer ishga tushganmi? (tray ikonkasi yashil bo'lsin)
echo    2. PHPMyAdmin'da 'sergak_ai' bazasi yaratilganmi?
echo       (http://localhost/phpmyadmin/ -^> Baza yaratish -^> sergak_ai)
echo.
pause

echo.
echo Python topilmoqda...

REM Try py launcher first (most reliable)
py -V >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=py"
    goto :run
)

REM Try direct path
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe" (
    set "PYCMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe"
    goto :run
)
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PYCMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe"
    goto :run
)
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYCMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
    goto :run
)

REM Fallback
python -V >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=python"
    goto :run
)

echo.
echo [!] Python topilmadi. Avval Python o'rnating: https://www.python.org/
pause
exit /b 1

:run
echo Python topildi: %PYCMD%
echo.
echo Migratsiya boshlanmoqda...
echo ================================================================
echo.

%PYCMD% migrate_to_mysql.py

echo.
echo ================================================================
if errorlevel 1 (
    echo [!] Migratsiya XATO bilan tugadi
) else (
    echo [OK] Migratsiya tugadi
    echo.
    echo Keyingi qadam: .env faylda DB_URL ni o'zgartiring va backendni qayta ishga tushiring.
    echo Buning uchun 2_start_backend.bat fayldan foydalaning.
)
echo ================================================================
echo.
pause
