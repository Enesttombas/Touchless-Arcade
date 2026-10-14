@echo off
setlocal enabledelayedexpansion
:: Gunluk stant baslatici (HP masaustunde cift tikla; yonetici gerekmez).
:: 1) kamera koprusunu kucultulmus pencerede baslatir (log: C:\stand\kopru.log)
:: 2) Moonlight ile laptopun ekranini 1080p60 acar.
:: Ilk kurulum icin once HP-KUR.cmd (yonetici) calistirilmis olmali.

set "STAND=C:\stand"
set "LOG=%STAND%\kopru.log"
set "LAPTOP=192.168.77.1"
set "HP_IP=192.168.77.2"

:: --- kamera_kopru.py: once C:\stand, sonra bu betigin yani, sonra depo yerlesimi
set "KOPRU="
for %%P in ("%STAND%\kamera_kopru.py" "%~dp0kamera_kopru.py" "%~dp0..\prototipler\kamera_kopru.py") do (
    if not defined KOPRU if exist "%%~P" set "KOPRU=%%~fP"
)
if not defined KOPRU (
    echo HATA: kamera_kopru.py bulunamadi. Once HP-KUR.cmd calistir.
    pause & exit /b 1
)

:: --- Python: HP_PYTHON, sonra PATH'teki python, sonra py baslaticisi
set "PY=%HP_PYTHON%"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul ^| findstr /v /i WindowsApps') do if not defined PY set "PY=%%P"
if not defined PY for /f "delims=" %%P in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%P"
if not defined PY (
    echo HATA: Python bulunamadi. HP_PYTHON ortam degiskenine python.exe yolunu yaz.
    pause & exit /b 1
)

:: --- Moonlight: MOONLIGHT_EXE, C:\stand altinda tasinabilir surum, sonra Program Files
set "MOONLIGHT=%MOONLIGHT_EXE%"
if not defined MOONLIGHT for /r "%STAND%" %%M in (Moonlight.exe) do if not defined MOONLIGHT if exist "%%M" set "MOONLIGHT=%%M"
if not defined MOONLIGHT if exist "%ProgramFiles%\Moonlight Game Streaming\Moonlight.exe" set "MOONLIGHT=%ProgramFiles%\Moonlight Game Streaming\Moonlight.exe"
if not defined MOONLIGHT (
    echo HATA: Moonlight.exe bulunamadi ^(C:\stand altinda ya da Program Files^).
    pause & exit /b 1
)

:: --- Kablo kontrolu
ping -n 1 -w 1000 %LAPTOP% >nul
if errorlevel 1 (
    echo HATA: Laptop %LAPTOP% yanit vermiyor. Ethernet kablosu takili mi, laptopta ag_kur_laptop.ps1 calisti mi?
    pause & exit /b 1
)

:: --- Kamerayi tutan eski surecler (Kamera uygulamasi, eski HTTP yayini) kapatilir
taskkill /f /im WindowsCamera.exe >nul 2>&1
wmic process where "CommandLine like '%%kamera_yayin.py%%'" call terminate >nul 2>&1

:: --- Kopru zaten calisiyorsa ikinciyi acma
netstat -an | findstr /c:"%HP_IP%:8090" | findstr LISTENING >nul
if errorlevel 1 (
    echo Kamera koprusu baslatiliyor... ^(log: %LOG%^)
    if not defined HP_KAMERA_BOYUT set "HP_KAMERA_BOYUT=1280x720"
    start "MemeKopru" /min cmd /c ""%PY%" "%KOPRU%" --gonder --bind %HP_IP% --port 8090 --kamera 0 --boyut !HP_KAMERA_BOYUT! >> "%LOG%" 2>&1"
    timeout /t 3 /nobreak >nul
) else (
    echo Kamera koprusu zaten calisiyor.
)

:: --- Ekran yayini
"%MOONLIGHT%" stream %LAPTOP% Desktop --resolution 1920x1080 --fps 60 --bitrate 20000 --video-codec H.264 --no-vsync
exit /b 0
