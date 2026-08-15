@echo off
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo.
echo ================================================================
echo   SIGARET DATASETLARNI KONVERSIYA (v2)
echo ================================================================
echo.
echo   Kirish:  D:\sergak dasturi\sergak_smoking\datasets\
echo   Chiqish: D:\sergak dasturi\sergak_smoking\prepared\
echo.
echo   6 ta IDEAL datasetni 2-klassli YOLO formatga keltirish:
echo     0 = smoking      (sigaret chekayotgan)
echo     1 = no_smoking   (sigaretsiz)
echo.
echo   Datasetlar:
echo     - rbf_archive                     1,030
echo     - rbf_final_smoking_v3           43,070  (ENG KATTA!)
echo     - rbf_smoking_people_v2           3,547
echo     - rbf_smoking_smoker1             8,407
echo     - rbf_smoking_v1                  6,804
echo     - Smoking-CCTV-Detection_v1         207
echo     ---------------------------------------
echo     JAMI:                            63,065 rasm
echo.
echo   Vaqt: 10-20 daqiqa
echo.
pause

echo.
%PYCMD% scripts\prepare_smoking_v2.py

echo.
pause
