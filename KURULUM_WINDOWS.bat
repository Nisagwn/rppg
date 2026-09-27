@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
setlocal
cd /d "%~dp0"
echo ============================================================
echo   Temassiz Nabiz (rPPG) Projesi - Windows Kurulumu
echo ============================================================
echo.

REM --- Python bul: once 3.12/3.11/3.10 (py launcher), sonra PATH'teki python, sonra Anaconda
setlocal enabledelayedexpansion
set "PY="
for %%v in (3.12 3.11 3.10 3.13) do (
  if not defined PY (
    py -%%v --version >nul 2>nul && set "PY=py -%%v"
  )
)
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY if exist "%USERPROFILE%\anaconda3\python.exe" set "PY=%USERPROFILE%\anaconda3\python.exe"
if not defined PY if exist "%USERPROFILE%\miniconda3\python.exe" set "PY=%USERPROFILE%\miniconda3\python.exe"
if not defined PY (
  echo [HATA] Python bulunamadi. https://www.python.org/downloads/ adresinden
  echo        Python 3.11 kurun ve "Add python.exe to PATH" kutusunu isaretleyin.
  pause
  exit /b 1
)
echo [1/5] Python:
%PY% --version

echo [2/5] Sanal ortam olusturuluyor (.venv)...
if not exist .venv (
  !PY! -m venv .venv || ( echo [HATA] venv olusturulamadi & pause & exit /b 1 )
)
call .venv\Scripts\activate.bat

echo [3/5] Kutuphaneler kuruluyor (birkac dakika surebilir)...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt || ( echo [HATA] pip install basarisiz & pause & exit /b 1 )

echo [4/5] Testler calistiriliyor...
python -m pytest -q -m "not slow"

echo [5/5] Ornek sentetik videolar uretiliyor (data\ornek_*.avi)...
python scripts\generate_sample.py --duration 30

echo.
echo ============================================================
echo  KURULUM TAMAM. Kullanim icin CALISTIR.bat dosyasini acin.
echo ============================================================
pause
