@echo off
rem Touchless Arcade: cift tikla ve oyna.
rem Ilk acilista oyun kendi tasinabilir Python'unu app\python icine kurar (internet gerekir, birkac dakika surer).
rem Bilgisayarda Python kurulu olmasi gerekmez. Sonraki acilislar aninda baslar.
rem BASLAT.bat --kur : yalniz kurar, oyunu acmaz (otomatik test icin).
cd /d "%~dp0"

set "PY=app\python\python.exe"
rem Eski surumlerle kurulmus app\.venv varsa onu kullan
if not exist "%PY%" if exist app\.venv\Scripts\python.exe set "PY=app\.venv\Scripts\python.exe"

if exist "%PY%" goto hazir
echo.
echo  Touchless Arcade ilk kez aciliyor.
echo  Oyunun calismasi icin gerekenler indirilip bu klasore kuruluyor (yaklasik 3-5 dakika).
echo  Bilgisayarina baska bir sey yuklenmez.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "app\kur.ps1"
if errorlevel 1 goto hata
set "PY=app\python\python.exe"

:hazir
if /i "%~1"=="--kur" exit /b 0
"%PY%" oyunlar\stant_app.py %*
if errorlevel 1 (
  echo Uygulama bir hatayla kapandi. Cozum onerileri: docs\troubleshooting.md
  pause
)
exit /b 0

:hata
if /i not "%~1"=="--kur" pause
exit /b 1
