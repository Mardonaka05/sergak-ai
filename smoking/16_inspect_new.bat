@echo off
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
    set "PIPCMD=..\kaska\venv\Scripts\pip.exe"
) else (
    set "PYCMD=py"
    set "PIPCMD=py -m pip"
)

echo.
echo ================================================================
echo   YANGI joylashuvdagi 85,634 rasmni TAHLIL QILISH
echo ================================================================
echo.
echo   Joylashuv: D:\sergak dasturi\sergak_smoking\datasets\
echo.
echo   Skript har bir dataset uchun:
echo     1. Klasslarni aniqlaydi (yaml + folder + filename)
echo     2. Klass boyicha rasm sonini sanaydi
echo     3. 8 ta NAMUNA rasm tanlaydi
echo     4. HTML hisobot yaratadi
echo     5. Verdict: USE / CHECK / SKIP
echo.
echo   Vaqt: 5-10 daqiqa
echo.
pause

echo.
echo [+] Pillow library tekshirilmoqda...
%PIPCMD% install -q --disable-pip-version-check Pillow

echo.
%PYCMD% scripts\ideal_inspect.py

echo.
echo ================================================================
echo   TUGADI
echo ================================================================
echo.

if exist "D:\sergak dasturi\sergak_smoking\inspection_report.html" (
    echo HTML hisobot tayyor - brauzerda ochilmoqda...
    start "" "D:\sergak dasturi\sergak_smoking\inspection_report.html"
)

echo.
pause
