@echo off
chcp 65001 >nul
title Sigaret Datasetlar IDEAL Retry (E: diskka)
cd /d "%~dp0"

if exist "..\kaska\venv\Scripts\python.exe" (
    set "PYCMD=..\kaska\venv\Scripts\python.exe"
    set "PIPCMD=..\kaska\venv\Scripts\pip.exe"
) else (
    set "PYCMD=py"
    set "PIPCMD=py -m pip"
)

REM ===== TOKENLAR (avtomatik o'rnatilgan) =====
set "ROBOFLOW_API_KEY=FKDfvXn5w6CGC4khaxPF"
set "KAGGLE_API_TOKEN=KGAT_7f6d388560bec29c6ac64aeb06cc09e5"

echo ================================================================
echo   Sergak AI - SIGARET datasetlarni IDEAL RETRY v5.0
echo ================================================================
echo.
echo   Manzil:      E:\sergak_smoking\datasets\
echo   Manbalar:    HuggingFace + Kaggle (10 ta) + Roboflow (tezkor)
echo   Tokenlar:    o'rnatilgan
echo.
echo   Bu safar:
echo     - Bo'sh papkalar tozalanadi
echo     - Avval yuklab olinganlar SKIP qilinadi
echo     - Kaggle 10 ta dataset sinaladi (oldingi 5 + yangi 5)
echo     - Roboflow tezda sinab ko'rib o'tib ketadi (vaqt yo'qotmaymiz)
echo.

REM E:\ disk tekshirish
if exist "E:\" (
    if not exist "E:\sergak_smoking" mkdir "E:\sergak_smoking"
    if not exist "E:\sergak_smoking\datasets" mkdir "E:\sergak_smoking\datasets"
    echo [+] E:\sergak_smoking\ tayyor
) else (
    echo [!] E:\ disk topilmadi - D:\ ga saqlanadi
)

REM Kaggle token saqlash (yangi format)
if not exist "%USERPROFILE%\.kaggle" mkdir "%USERPROFILE%\.kaggle"
echo|set /p="%KAGGLE_API_TOKEN%" > "%USERPROFILE%\.kaggle\access_token"
echo [+] Kaggle token saqlandi

echo.
echo [+] Paketlarni yangilash...
%PIPCMD% install -q --disable-pip-version-check --upgrade kaggle huggingface_hub
%PIPCMD% install -q --disable-pip-version-check roboflow datasets requests tqdm

echo.
echo ================================================================
echo   Yuklab olish boshlandi...
echo ================================================================
echo.

%PYCMD% scripts\auto_download.py

echo.
echo ================================================================
echo   TUGADI
echo ================================================================
echo.

if exist "E:\sergak_smoking\datasets" (
    echo Tekshirish: explorer "E:\sergak_smoking\datasets"
)
echo.
echo Keyingi qadam:
echo   - Agar 30,000+ rasm bo'lsa: prepare_smoking.py yarataman
echo   - Agar kam bo'lsa: Roboflow'ni qo'lda yuklab oling (linklar yuqorida)
echo.
pause
