@echo off
rem Stant Kamera Oyunlari: cift tikla ve oyna.
rem Ilk acilista paketleri kendisi kurar (internet gerekir, birkac dakika surer); sonraki acilislar aninda baslar.
cd /d "%~dp0"

if exist app\.venv\Scripts\python.exe goto basla

echo [1/2] Ilk kurulum: Python 3.11 araniyor...
set "PY_CMD="
py -3.11 --version >nul 2>&1 && set "PY_CMD=py -3.11"
if not defined PY_CMD (
  python --version 2>nul | findstr /R "3\.11" >nul 2>&1 && set "PY_CMD=python"
)
if not defined PY_CMD (
  echo.
  echo Python 3.11 bulunamadi.
  echo https://www.python.org/downloads/release/python-3119/ adresinden kurun
  echo ^(kurulumda "Add python.exe to PATH" kutusunu isaretleyin^), sonra BASLAT.bat'i tekrar acin.
  pause
  exit /b 1
)

echo [2/2] Paketler kuruluyor, birkac dakika surebilir...
%PY_CMD% -m venv app\.venv || goto hata
app\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
app\.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt || goto hata
echo Kurulum tamam.

:basla
app\.venv\Scripts\python.exe oyunlar\stant_app.py %*
if errorlevel 1 (
  echo Uygulama bir hatayla kapandi. Cozum onerileri: docs\troubleshooting.md
  pause
)
exit /b 0

:hata
echo.
echo Kurulum basarisiz. Internet baglantisini kontrol edip BASLAT.bat'i tekrar acin.
if exist app\.venv rmdir /s /q app\.venv
pause
exit /b 1
