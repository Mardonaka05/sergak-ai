@echo off
chcp 65001 >nul
title Sergak AI - GUI Test Application
cd /d "%~dp0"

if exist "venv\Scripts\pythonw.exe" (
    set "PYW=venv\Scripts\pythonw.exe"
    set "PYCMD=venv\Scripts\python.exe"
) else (
    set "PYW=pyw"
    set "PYCMD=py"
)

echo ================================================================
echo   Sergak AI - GUI Test Application
echo ================================================================
echo.
echo   Imkoniyatlari:
echo     - Web kamera (real-time)
echo     - Video fayl tanlash (file dialog)
echo     - Rasm fayl tanlash
echo     - Rasmlar papkasi
echo     - Confidence slider
echo     - Snapshot, Pauza, Keyingi tugmalari
echo.
echo   Konsol oynasi yopilmaydi (xato bo'lsa shu yerda ko'rinadi).
echo ================================================================
echo.

%PYCMD% scripts\test_gui.py

echo.
echo Dastur yopildi.
pause
