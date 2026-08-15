@echo off
chcp 65001 >nul
title Sigaret Loyihasi - Boshlang'ich sozlash
cd /d "%~dp0"

echo ================================================================
echo   Sergak AI - Sigaret Aniqlash Loyihasi
echo ================================================================
echo.
echo   Bu skript loyiha papkalarini yaratadi.
echo.
echo   Joylashish: %CD%
echo.
pause

echo.
echo [+] Papkalarni yaratish...

if not exist "datasets" mkdir "datasets"
if not exist "merged" mkdir "merged"
if not exist "scripts" mkdir "scripts"
if not exist "runs" mkdir "runs"

echo [OK] datasets\   - bu yerga ZIP fayllarni qo'ying
echo [OK] merged\     - yakuniy birlashtirilgan dataset
echo [OK] scripts\    - konversiya skriptlari
echo [OK] runs\       - training natijalari

echo.
echo ================================================================
echo   KEYINGI QADAMLAR
echo ================================================================
echo.
echo   1. README.md ni o'qing - barcha datasetlar ro'yxati bor
echo.
echo   2. Quyidagi 4 ta datasetni yuklab oling:
echo.
echo      a) Smoker YOLO (Roboflow):
echo         https://universe.roboflow.com/cigaretteple-7m0hn/smoker-yolo
echo.
echo      b) Smoking-Drinking (Kaggle):
echo         https://www.kaggle.com/datasets/prajjwalkumarpanzade/smoking-and-drinking-dataset-for-yolo
echo.
echo      c) Cigarette Detection (Roboflow):
echo         https://universe.roboflow.com/yolo-pdvpx/cigarette-h2p1m
echo.
echo      d) Smoking-Drinking Detection (Roboflow):
echo         https://universe.roboflow.com/yolo-dataset-rtznj/smoking-and-drinking-detection
echo.
echo   3. ZIP fayllarni datasets\ papkasiga extract qiling:
echo         datasets\roboflow_smoker_yolo\
echo         datasets\kaggle_smoking_drinking\
echo         datasets\roboflow_cigarette\
echo         datasets\roboflow_smoking_drinking\
echo.
echo   4. Tekshirish: 2_check.bat ni ishga tushiring
echo.
pause
