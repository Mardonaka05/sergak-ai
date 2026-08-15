@echo off
chcp 65001 >nul
title Sergak AI - Paketlarni o'rnatish
cd /d "%~dp0"

echo ================================================================
echo   Sergak AI - Kerakli paketlarni o'rnatish
echo ================================================================
echo.

REM Find Python
py -V >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=py"
    goto :found
)
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe" (
    set "PYCMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe"
    goto :found
)
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PYCMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe"
    goto :found
)
python -V >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=python"
    goto :found
)
echo [!] Python topilmadi
pause
exit /b 1

:found
echo Python: %PYCMD%
echo.

REM Noto'g'ri "jwt" paketini avtomatik olib tashlash (PyJWT kerak edi)
echo [1/2] Noto'g'ri 'jwt' paketini olib tashlash (agar bor bo'lsa)...
%PYCMD% -m pip uninstall jwt -y 2>nul
echo.

echo [2/2] requirements.txt dagi paketlarni o'rnatish...
echo.
%PYCMD% -m pip install -r requirements.txt --break-system-packages

echo.
echo ================================================================
if errorlevel 1 (
    echo [!] O'rnatish XATO bilan tugadi
) else (
    echo [OK] Hamma paketlar o'rnatildi
    echo.
    echo Endi backendni ishga tushiring:
    echo   2_start_backend.bat ga ikki marta bosing
)
echo ================================================================
pause
