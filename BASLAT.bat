@echo off
rem Kaynaktan calistirma: Derlenmis Stant.exe olmadan da dogrudan Python uzerinden acar.
cd /d "%~dp0"
if not exist app\.venv\Scripts\python.exe (
  echo HATA: Sanal ortam app\.venv bulunamadi. Once KUR.bat calistirin.
  pause
  exit /b 1
)
app\.venv\Scripts\python.exe prototipler\stant_app.py %*
set "EXIT_CODE=%ERRORLEVEL%"
if %EXIT_CODE% neq 0 (
  echo Uygulama bir hata ile kapandi. Hata kodu: %EXIT_CODE%
  pause
  exit /b %EXIT_CODE%
)
exit /b 0
