@echo off
chcp 65001 >nul
title GPU + PyTorch sozlash
cd /d "%~dp0"

if exist "..\backend\venv\Scripts\python.exe" (
    set "PYCMD=..\backend\venv\Scripts\python.exe"
    set "PIPCMD=..\backend\venv\Scripts\pip.exe"
    echo [+] backend venv ishlatilmoqda
) else (
    set "PYCMD=py"
    set "PIPCMD=py -m pip"
    echo [+] tizim python ishlatilmoqda
)

echo.
echo ================================================================
echo   BOSQICH 1/3: NVIDIA GPU va PyTorch tekshiruvi
echo ================================================================
%PYCMD% scripts\check_gpu.py
set CHECK_RESULT=%ERRORLEVEL%

if %CHECK_RESULT% EQU 0 (
    echo.
    echo [OK] GPU tayyor - boshqa hech narsa kerak emas!
    echo.
    echo Endi treningni boshlashingiz mumkin:
    echo   .\7_train.bat
    echo.
    pause
    exit /b 0
)

echo.
echo ================================================================
echo   BOSQICH 2/3: CUDA-li PyTorch o'rnatish kerakmi?
echo ================================================================
echo.
echo   Eski PyTorch ni o'chirib, CUDA 12.1 ni o'rnatamiz.
echo   Bu ~3 GB yuklaydi (vaqt: 5-15 daqiqa internet tezligiga qarab).
echo.
choice /M "Davom etaylikmi"
if errorlevel 2 (
    echo Bekor qilindi.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   BOSQICH 3/3: PyTorch CUDA 12.1 o'rnatilmoqda
echo ================================================================
echo.
echo [+] Eski PyTorch o'chirilmoqda...
%PIPCMD% uninstall torch torchvision torchaudio -y

echo.
echo [+] PyTorch CUDA 12.1 o'rnatilmoqda...
%PIPCMD% install torch torchvision --index-url https://download.pytorch.org/whl/cu121

if errorlevel 1 (
    echo.
    echo [X] O'rnatish xato bilan tugadi!
    echo     Internet aloqasini tekshiring.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   ULTRALYTICS o'rnatish
echo ================================================================
%PIPCMD% install ultralytics

echo.
echo ================================================================
echo   QAYTA TEKSHIRUV
echo ================================================================
%PYCMD% scripts\check_gpu.py

if errorlevel 1 (
    echo.
    echo [!] Hali ham GPU ko'rinmayapti. Quyidagilarni tekshiring:
    echo   1. NVIDIA drayveri yangilanganmi? https://nvidia.com/drivers
    echo   2. Windows qayta yuklab ko'ring
    echo   3. nvidia-smi cmd da ishlaydimi?
) else (
    echo.
    echo [OK] HAMMASI TAYYOR! Endi training boshlashingiz mumkin:
    echo   .\7_train.bat
)
echo.
pause
