@echo off
rem Yeni bilgisayarda bir kez calistir: app\.venv olusturur ve paketleri kurar (internet gerekir).
rem On kosul: Python 3.11 (python.org, "py launcher" secili).
cd /d "%~dp0"
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo HATA: Python 3.11 bulunamadi. https://www.python.org/downloads/release/python-3119/ adresinden kur, sonra tekrar calistir.
  pause
  exit /b 1
)
if not exist app\.venv\Scripts\python.exe py -3.11 -m venv app\.venv
app\.venv\Scripts\python.exe -m pip install --upgrade pip
app\.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo HATA: paket kurulumu basarisiz.
  pause
  exit /b 1
)
echo Kurulum tamam. Stant.exe ile ac.
pause
