@echo off
chcp 65001 >nul
title Sergak AI Backend
cd /d "%~dp0"

echo ================================================================
echo   Sergak AI Backend
echo ================================================================
echo.

REM Find Python
py -V >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=py"
    goto :run
)
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe" (
    set "PYCMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe"
    goto :run
)
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PYCMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe"
    goto :run
)
python -V >nul 2>&1
if not errorlevel 1 (
    set "PYCMD=python"
    goto :run
)
echo [!] Python topilmadi.
pause
exit /b 1

:run
echo Python: %PYCMD%
echo.
%PYCMD% -m app.main

echo.
echo Backend to'xtadi. Yopish uchun istalgan tugmani bosing.
pause
