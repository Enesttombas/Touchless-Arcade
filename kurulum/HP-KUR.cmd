@echo off
setlocal enabledelayedexpansion
:: HP ilk kurulum (bir kez, YONETICI cmd). USB'deki kurulum klasorunden calistir:
::   1) kamera_kopru.py ve Stant-HP.bat'i C:\stand'e kopyalar, masaustune kisayol koyar
::   2) ag_kur_hp.cmd ile 192.168.77.2 + guvenlik duvari kurali
::   3) Python + OpenCV kontrolu, kamera taramasi (kamera_tara.txt)
::   4) Moonlight'i laptopla esler (PIN 4821, laptopta Sunshine web arayuzune girilir)
:: Kullanim: HP-KUR.cmd [bagdastirici_adi]   (varsayilan: Ethernet)

set "STAND=C:\stand"
set "ADAPTER=%~1"
if "%ADAPTER%"=="" set "ADAPTER=Ethernet"

fltmc >nul 2>&1
if errorlevel 1 (
    echo HATA: Yonetici olarak calistir ^(sag tik, Yonetici olarak calistir^).
    pause & exit /b 1
)

:: --- 1) Dosyalar
if not exist "%STAND%" mkdir "%STAND%"
set "KAYNAK="
for %%P in ("%~dp0kamera_kopru.py" "%~dp0..\prototipler\kamera_kopru.py") do (
    if not defined KAYNAK if exist "%%~P" set "KAYNAK=%%~fP"
)
if not defined KAYNAK (
    echo HATA: kamera_kopru.py bu klasorde yok. USB'ye kurulum klasoruyle birlikte kopyala.
    pause & exit /b 1
)
copy /y "%KAYNAK%" "%STAND%\kamera_kopru.py" >nul || (echo HATA: kopyalama & pause & exit /b 1)
copy /y "%~dp0Stant-HP.bat" "%STAND%\Stant-HP.bat" >nul || (echo HATA: kopyalama & pause & exit /b 1)
copy /y "%STAND%\Stant-HP.bat" "%PUBLIC%\Desktop\Stant-HP.bat" >nul
echo [1/4] Dosyalar C:\stand altinda, masaustunde Stant-HP.bat var.

:: --- 2) Ag
call "%~dp0ag_kur_hp.cmd" "%ADAPTER%"
if errorlevel 1 (
    echo Bagdastirici adlari:
    netsh interface show interface
    echo Dogru adla tekrar: HP-KUR.cmd "Ad"
    pause & exit /b 1
)
echo [2/4] Ag tamam: 192.168.77.2

:: --- 3) Python + OpenCV + kamera taramasi
set "PY=%HP_PYTHON%"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul ^| findstr /v /i WindowsApps') do if not defined PY set "PY=%%P"
if not defined PY for /f "delims=" %%P in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%P"
if not defined PY (
    echo HATA: Python yok. HP_PYTHON=python.exe yolu ile tekrar calistir.
    pause & exit /b 1
)
"%PY%" -c "import cv2, numpy; print('OpenCV', cv2.__version__)"
if errorlevel 1 (
    echo HATA: OpenCV/numpy yok. Internete bagliyken: "%PY%" -m pip install opencv-python numpy
    pause & exit /b 1
)
setx HP_PYTHON "%PY%" >nul
taskkill /f /im WindowsCamera.exe >nul 2>&1
wmic process where "CommandLine like '%%kamera_yayin.py%%'" call terminate >nul 2>&1
echo [3/4] Kamera taraniyor ^(~1 dk^)...
"%PY%" "%STAND%\kamera_kopru.py" --tara --kamera 0 --sure 3 > "%STAND%\kamera_tara.txt" 2>&1
type "%STAND%\kamera_tara.txt"

:: --- 4) Moonlight eslesmesi
set "MOONLIGHT=%MOONLIGHT_EXE%"
if not defined MOONLIGHT for /r "%STAND%" %%M in (Moonlight.exe) do if not defined MOONLIGHT if exist "%%M" set "MOONLIGHT=%%M"
if not defined MOONLIGHT if exist "%ProgramFiles%\Moonlight Game Streaming\Moonlight.exe" set "MOONLIGHT=%ProgramFiles%\Moonlight Game Streaming\Moonlight.exe"
if not defined MOONLIGHT (
    echo UYARI: Moonlight.exe bulunamadi; C:\stand altina tasinabilir surumu koy.
    pause & exit /b 1
)
echo [4/4] Eslestirme: laptopta https://localhost:47990 ^> PIN sekmesine 4821 yaz.
"%MOONLIGHT%" pair 192.168.77.1 --pin 4821
echo.
echo Kurulum bitti. Her gun: masaustundeki Stant-HP.bat.
pause
exit /b 0
