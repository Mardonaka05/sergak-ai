@echo off
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo.
echo ================================================================
echo   ZIP EXTRACT va D:\sergak dasturi\sergak_smoking ga KO'CHIRISH
echo ================================================================
echo.
echo   Source:  E:\sergak_smoking\
echo   Target:  D:\sergak dasturi\sergak_smoking\datasets\
echo.
echo   Skript quyidagilarni qiladi:
echo     1. 7 ta ZIP faylni extract qiladi
echo     2. Yaxshi datasetlarni D: ga ko'chiradi
echo     3. Junk papkalarni skip qiladi (znd_indoor_smoke, gh_*)
echo     4. Hisobot beradi
echo.
echo   ZIP fayllar (~3.3 GB):
echo     - final_smoking.v3i.yolov8.zip          1690 MB
echo     - Smoking Detection.v5i.yolov8.zip       710 MB
echo     - smoking.v1-smoker1.yolov8.zip          358 MB
echo     - smoking.v1i.yolov8.zip                 179 MB
echo     - smoking detection.v1i.yolov8.zip       174 MB
echo     - smoking people.v2i.yolov8.zip          170 MB
echo     - archive.zip                             24 MB
echo.
echo   Vaqt: 5-15 daqiqa (disk tezligiga bog'liq)
echo.
echo   D: diskda kamida 4 GB bo'sh joy kerak!
echo.

choice /M "Davom etamizmi"
if errorlevel 2 (
    echo Bekor qilindi.
    pause
    exit /b 0
)

echo.
%PYCMD% scripts\extract_and_organize.py

echo.
echo ================================================================
echo   TUGADI
echo ================================================================
echo.
if exist "D:\sergak dasturi\sergak_smoking\datasets" (
    echo Tekshirish: explorer "D:\sergak dasturi\sergak_smoking\datasets"
)
echo.
pause
