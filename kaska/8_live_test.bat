@echo off
chcp 65001 >nul
title Sergak AI - Real-time Test (kamera / video / rasm)
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    set "PYCMD=venv\Scripts\python.exe"
) else if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   Sergak AI - Real-time Kaska Aniqlash Test
echo ================================================================
echo.
echo   Manba tanlang:
echo     1 = Web kamera (real-time)
echo     2 = Video fayl
echo     3 = Rasm fayl
echo     4 = Rasmlar papkasi
echo.
echo   DIQQAT: Hozir training davom etyapti - GPU band.
echo   Test --device cpu bilan ishlatiladi (sekinroq, lekin ishlaydi).
echo.

%PYCMD% scripts\live_test.py --device cpu

echo.
pause
