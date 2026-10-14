@echo off
REM Stant ekrani: laptop kamerasi (1), tam ekran. Harici kamera icin once "set KAMERA=0" (veya 2) yaz.
cd /d "%~dp0"
if "%KAMERA%"=="" set KAMERA=1
set TAM_EKRAN=1
"..\app\.venv\Scripts\python.exe" stand.py 2>> stand_hata.txt
