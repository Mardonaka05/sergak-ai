@echo off
chcp 65001 >nul
title Eski kameralarni tozalash
cd /d "%~dp0"

echo ================================================================
echo   Eski soxta kameralarni (192.168.1.x) tozalash
echo ================================================================
echo.
echo   Bu skript soxta (seed paytida yaratilgan) kameralarni
echo   o'chiradi va faqat 192.168.5.10 NVR kameralarini qoldiradi.
echo.
echo   Backend hozir TO'XTATILGAN bo'lishi kerak!
echo.
pause

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe cleanup_old_cameras.py
) else (
    py cleanup_old_cameras.py
)

echo.
pause
