@echo off
cd /d "%~dp0"
if "%KAMERA%"=="" set KAMERA=1
set TAM_EKRAN=1
..\app\.venv\Scripts\python.exe gezgin.py
