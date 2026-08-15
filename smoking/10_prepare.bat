@echo off
chcp 65001 >nul
title Sigaret datasetlarni KONVERTATSIYA
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo ================================================================
echo   Sigaret datasetlarni KONVERTATSIYA (folder/YOLO -^> YOLO 2-klass)
echo ================================================================
echo.
echo   Kirish:  E:\sergak_smoking\datasets\
echo   Chiqish: E:\sergak_smoking\prepared\
echo.
echo   Konvertatsiya rejasi:
echo     0 = smoking      (sigaret chekayotgan / sigaret object)
echo     1 = no_smoking   (oddiy odam, sigaretsiz)
echo.
echo   6 ta dataset konvertatsiya qilinadi:
echo     1. kgl_cigarette_smoker_dataset    (folder)
echo     2. mnd_smoker_detection            (folder)
echo     3. mnd_smoking_not_smoking         (folder)
echo     4. kgl_smoking_and_drinking_yolo   (YOLO)
echo     5. gh_smoking_meera                (YOLO)
echo     6. mnd_cigdet                      (YOLO no yaml)
echo.

%PYCMD% scripts\prepare_smoking.py

echo.
pause
