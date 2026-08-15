@echo off
chcp 65001 >nul
title Sergak AI - Kaska modeli treningi (YOLOv8l, 150 epoch)
cd /d "%~dp0"

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   Sergak AI - Kaska aniqlash modeli treningi
echo ================================================================
echo   Model:    YOLOv8l (large)
echo   Dataset:  65,154 rasm / 432,696 bbox
echo   Epochs:   150
echo   Image:    640 x 640
echo   Batch:    6 (8GB GPU uchun)
echo.
echo   Taxminiy vaqt: 24-40 soat (RTX 3060/4060/2080 da)
echo   Eng yaxshi vazn: D:\sergak dasturi\kaska\runs\helmet_v8l_640\weights\best.pt
echo ================================================================
echo.
echo   Boshlashdan oldin tekshiruv:
echo   1. ultralytics o'rnatilganmi?  (pip install ultralytics)
echo   2. CUDA va PyTorch ishlaydimi?
echo   3. Disk bo'sh joy 20+ GB (logs va checkpointlar uchun)
echo.
echo   Ctrl+C bilan istalgan vaqtda to'xtatish mumkin.
echo   Davom ettirish: %PYCMD% scripts\train.py --resume
echo.
pause

%PYCMD% scripts\train.py

echo.
echo ================================================================
echo   TRAINING JARAYONI TUGADI
echo ================================================================
echo.
echo   Natijani ko'rish:
echo     D:\sergak dasturi\kaska\runs\helmet_v8l_640\
echo.
echo   Inference test qilish:
echo     %PYCMD% scripts\test_inference.py
echo.
pause
