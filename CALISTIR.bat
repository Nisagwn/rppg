@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo Once KURULUM_WINDOWS.bat dosyasini calistirin.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
:menu
cls
echo ============================================================
echo   Temassiz Nabiz (rPPG) Projesi
echo ============================================================
echo   1) Canli demo (webcam)
echo   2) Canli demo - ornek sentetik video (kamera gerekmez)
echo   3) Ornek videoyu analiz et (grafikler results\run)
echo   4) EVM videosu uret (nabzi gorunur kil)
echo   5) Kendi verini kaydet (veri toplama oturumu)
echo   6) Sentetik benchmark (hizli, ~5 dk)
echo   7) Sentetik benchmark (tam, ~20-40 dk)
echo   8) UBFC-rPPG degerlendirmesi (data\UBFC altina indirdiyseniz)
echo   9) Testleri calistir
echo   D) UBFC-rPPG veri setini indir (5 denek)
echo   G) MCD-rPPG: 10 kisiyi indir + degerlendir (webcam/telefon, dinlenme/egzersiz)
echo   R) Raporu derle (docs\05_rapor.docx)
echo   M) Maske deneyi (kendi yuz fotografinla)
echo   0) Cikis
echo.
set /p c="Seciminiz: "
if "%c%"=="1" python scripts\live_demo.py
if "%c%"=="2" python scripts\live_demo.py --video data\ornek_hard.avi --bbox 104.2 51.2 111.5 121.8
if "%c%"=="3" python scripts\run_video.py --video data\ornek_hard.avi --bbox 104.2 51.2 111.5 121.8 --out results\run && start "" results\run
if "%c%"=="4" python scripts\make_evm_video.py --video data\ornek_ideal.avi --out results\evm.mp4 --alpha 120 && start "" results\evm.mp4
if "%c%"=="5" goto kayit
if "%c%"=="6" python scripts\synthetic_benchmark.py --quick --out results\synthetic_quick
if "%c%"=="7" python scripts\synthetic_benchmark.py --seeds 3 --duration 60 --out results\synthetic
if "%c%"=="8" python scripts\evaluate_ubfc.py --root data\UBFC --out results\ubfc
if "%c%"=="9" python -m pytest -q
if /i "%c%"=="D" python scripts\download_ubfc.py --subjects 5
if /i "%c%"=="G" python scripts\evaluate_mcd.py --download 10 --out results\mcd
if /i "%c%"=="R" python scripts\build_report.py && start "" docs\05_rapor.docx
if /i "%c%"=="M" goto maske
if "%c%"=="0" exit /b 0
echo.
pause
goto menu

:maske
set /p img="Yuz fotografi yolu (or. C:\Users\nisa\Pictures\selfie.jpg): "
python scripts\mask_experiment.py --image "%img%" --trials 4
pause
goto menu

:kayit
echo Kosullar: gunisigi_sabit, floresan_sabit, los_isik, ekran_isigi, konusma, bas_hareketi, egzersiz_sonrasi
set /p s="Denek kodu (or. K01): "
set /p k="Kosul: "
python scripts\record_session.py --subject %s% --condition %k% --duration 60
pause
goto menu
