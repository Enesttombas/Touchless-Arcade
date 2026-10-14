@echo off
rem Stant modu: 3x3 menude 3 oyun.
cd /d "%~dp0"
if "%KAMERA%"=="" set KAMERA=1
set TAM_EKRAN=1
..\app\.venv\Scripts\python.exe stant_app.py
