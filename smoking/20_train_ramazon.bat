@echo off
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo.
echo ================================================================
echo   Sergak AI - SIGARET TRAINING (Ramazon best.pt'dan)
echo ================================================================
echo.
echo   Model:    YOLOv8m (Ramazon kaska best.pt'dan transfer learning)
echo   Source:   D:\port\ramazon\best.pt (97.43%% mAP, kaska)
echo   Dataset:  ~60,000 rasm, ~93,000 smoking bbox
echo   Epochs:   100
echo   Image:    640 x 640
echo   Batch:    10 (YOLOv8m kichikroq, batch oshirildi)
echo   Klasslar: 1 (smoking)
echo.
echo   Eslatma: Klasslar moslashtirildi (2 -> 1)
echo   Vaqt:    12-18 soat
echo.
pause

%PYCMD% scripts\train_smoking.py --model "D:\port\ramazon\best.pt" --batch 10

echo.
echo ================================================================
echo   TRAINING TUGADI
echo ================================================================
pause
