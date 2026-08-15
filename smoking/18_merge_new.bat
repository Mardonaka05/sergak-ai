@echo off
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
) else (
    set "PYCMD=py"
)

echo.
echo ================================================================
echo   SIGARET DATASETLAR YAKUNIY MERGE (80/15/5 split)
echo ================================================================
echo.
echo   Input:   D:\sergak dasturi\sergak_smoking\prepared\
echo   Output:  D:\sergak dasturi\sergak_smoking\merged\
echo.
echo   Skript quyidagilarni qiladi:
echo     1. 6 ta prepared papkadan rasmlarni yigadi
echo     2. 80%% train, 15%% val, 5%% test ga boladi
echo     3. data.yaml yaratadi (1 klass: smoking)
echo.
echo   Kutilgan natija:
echo     train: ~48,000 rasm
echo     val:    ~9,000 rasm
echo     test:   ~3,000 rasm
echo     JAMI:  ~60,000 rasm
echo.
echo   Vaqt: 10-20 daqiqa
echo.
pause

echo.
%PYCMD% scripts\final_merge_smoking_v2.py

echo.
pause
