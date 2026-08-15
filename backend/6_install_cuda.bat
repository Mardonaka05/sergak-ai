@echo off
cd /d "%~dp0"
chcp 65001 >nul 2>&1

if exist "venv\Scripts\python.exe" (
    set "PYCMD=venv\Scripts\python.exe"
    set "PIPCMD=venv\Scripts\pip.exe"
) else (
    echo [X] venv topilmadi! Avval venv yarating.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   SERGAK AI - PyTorch CUDA O'RNATISH (RTX GPU uchun)
echo ================================================================
echo.
echo   Hozirgi holat: CPU rejimi (sekin)
echo   Maqsad:        GPU CUDA 12.1 (3-5x tez)
echo.
echo   Bu skript:
echo     1. CPU-only torch ni olib tashlaydi
echo     2. CUDA 12.1 versiyasini yuklab oladi (~2-3 GB)
echo     3. CUDA test qiladi
echo.
echo   Talab:
echo     - NVIDIA GPU (RTX 20xx/30xx/40xx)
echo     - NVIDIA driver yangilangan bo'lishi kerak
echo     - Internet aloqasi (yuklash uchun)
echo     - Vaqt: 5-10 daqiqa
echo.
pause

echo.
echo === 1) NVIDIA GPU mavjudligini tekshirish ===
nvidia-smi
if errorlevel 1 (
    echo.
    echo [X] NVIDIA GPU topilmadi yoki driver yo'q!
    echo     Avval NVIDIA driver o'rnating: https://www.nvidia.com/drivers
    pause
    exit /b 1
)

echo.
echo === 2) Eski (CPU) torch ni olib tashlash ===
%PIPCMD% uninstall -y torch torchvision torchaudio
echo.

echo.
echo === 3) CUDA 12.1 versiyasini o'rnatish ===
echo     (~2-3 GB yuklab olinadi, sabr qiling)
%PIPCMD% install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 (
    echo.
    echo [!] CUDA 12.1 ishlamadi, CUDA 11.8 ga urinib ko'ramiz...
    %PIPCMD% install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
)

echo.
echo === 4) CUDA testi ===
%PYCMD% -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda if torch.cuda.is_available() else 'N/A'); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

echo.
echo === 5) Ultralytics qayta tekshirish ===
%PYCMD% -c "from ultralytics import YOLO; print('Ultralytics OK')"

echo.
echo ================================================================
echo   TAYYOR!
echo ================================================================
echo.
echo   Yuqorida CUDA available: True bo'lsa, GPU ishga tushdi!
echo   Endi backend ni qayta ishga tushiring:
echo     5_fix_and_start.bat
echo.
pause
