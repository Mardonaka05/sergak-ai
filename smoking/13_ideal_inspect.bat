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
echo   IDEAL DATASET TEKSHIRUVI (HTML hisobot bilan)
echo ================================================================
echo.
echo   Skript har bir dataset uchun:
echo     - Klasslarni aniqlaydi (folder/yaml/filename)
echo     - Klass boyicha rasm sonini sanaydi
echo     - 8 ta NAMUNA rasm tanlaydi
echo     - HTML hisobot yaratadi (thumbnail bilan)
echo     - Verdict beradi: USE / CHECK / SKIP
echo.
echo   Natija:
echo     E:\sergak_smoking\inspection_report.html
echo     (brauzerda ochib hamma rasmlarni korasiz)
echo.
pause

echo.
echo [+] Pillow library tekshirilmoqda...
%PIPCMD% install -q --disable-pip-version-check Pillow

echo.
echo [+] Tahlil boshlanmoqda (5-10 daqiqa)...
echo.

%PYCMD% scripts\ideal_inspect.py

echo.
echo ================================================================
echo   TUGADI
echo ================================================================
echo.

if exist "E:\sergak_smoking\inspection_report.html" (
    echo HTML hisobot tayyor - brauzerda ochilmoqda...
    start "" "E:\sergak_smoking\inspection_report.html"
) else if exist "D:\sergak dasturi\smoking\inspection_report.html" (
    echo HTML hisobot tayyor - brauzerda ochilmoqda...
    start "" "D:\sergak dasturi\smoking\inspection_report.html"
)

echo.
pause
