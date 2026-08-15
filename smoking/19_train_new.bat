@echo off
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo.
echo ================================================================
echo   Sergak AI - SIGARET ANIQLASH TRAINING (1 KLASS)
echo ================================================================
echo.
echo   Model:    YOLOv8l (Kaska best.pt'dan transfer learning)
echo   Dataset:  ~60,000 rasm, ~93,000 smoking bbox
echo   Epochs:   100 (transfer learning bilan tez)
echo   Image:    640 x 640
echo   Batch:    6 (8GB GPU uchun)
echo   Klasslar: 1 (smoking)
echo.
echo   Best.pt: D:\sergak dasturi\sergak_smoking\runs\smoking_v8l_640\weights\best.pt
echo.
echo   Taxminiy vaqt: 15-25 soat (RTX 4060 Laptop da)
echo   Kutilgan mAP@0.5: 92-95%%
echo.
echo   Ctrl+C bilan istalgan vaqtda toxtatish mumkin.
echo   Davom ettirish: %PYCMD% scripts\train_smoking.py --resume
echo.
pause

%PYCMD% scripts\train_smoking.py

echo.
echo ================================================================
echo   TRAINING TUGADI
echo ================================================================
echo.
echo   Natija: D:\sergak dasturi\sergak_smoking\runs\smoking_v8l_640\
echo.
pause
