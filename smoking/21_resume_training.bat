@echo off
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo.
echo ================================================================
echo   Sergak AI - SIGARET TRAINING DAVOM ETTIRISH (RESUME)
echo ================================================================
echo.
echo   Last.pt:  D:\sergak dasturi\sergak_smoking\runs\smoking_v8l_640\weights\last.pt
echo.
echo   Skript oxirgi saqlangan epoch'dan davom ettiradi.
echo   Hech narsa yo'qolmaydi - optimizer, lr, weights saqlangan.
echo.
echo   Tekshirish: avval last.pt holatini ko'ramiz...
echo.
pause

echo.
echo === LAST.PT TEKSHIRUVI ===
%PYCMD% scripts\check_pt.py "D:\sergak dasturi\sergak_smoking\runs\smoking_v8l_640\weights\last.pt"

echo.
echo === RESUME ===
echo.
pause

%PYCMD% scripts\train_smoking.py --resume

echo.
echo ================================================================
echo   TRAINING TUGADI
echo ================================================================
pause
