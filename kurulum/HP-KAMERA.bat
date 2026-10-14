@echo off
:: HP kamera koprusu tek adim kurulum + baslatma (YONETICI cmd). USB gerekmez:
:: dosyalar kablodan laptoptan (HP-Dagit.ps1, http://192.168.77.1:8765) cekilir.
:: HP'de yazilacak tek satir:
::   curl -o C:\stand\HP-KAMERA.bat http://192.168.77.1:8765/HP-KAMERA.bat && C:\stand\HP-KAMERA.bat
set "STAND=C:\stand"
set "SUNUCU=http://192.168.77.1:8765"
:: Istege bagli 1. arguman kamera boyutu (varsayilan 1280x720 = genis aci; takilirsa 640x360)
set "BOYUT=%~1"
if "%BOYUT%"=="" set "BOYUT=1280x720"
fltmc >nul 2>&1 || (echo HATA: Yonetici cmd ile calistir. & pause & exit /b 1)
if not exist "%STAND%" mkdir "%STAND%"

echo [1/4] Dosyalar laptoptan aliniyor...
for %%F in (kamera_kopru.py Stant-HP.bat) do (
    curl -s -f -o "%STAND%\%%F" "%SUNUCU%/%%F" || (echo HATA: %%F alinamadi. Laptopta HP-Dagit.ps1 acik mi? & pause & exit /b 1)
)
copy /y "%STAND%\Stant-HP.bat" "%PUBLIC%\Desktop\Stant-HP.bat" >nul

echo [2/4] Guvenlik duvari: 8090 yalniz laptoptan...
netsh advfirewall firewall delete rule name="MemeKameraHPKameraTCP" >nul 2>&1
netsh advfirewall firewall add rule name="MemeKameraHPKameraTCP" dir=in action=allow protocol=TCP localport=8090 localip=192.168.77.2 remoteip=192.168.77.1 profile=any >nul || (echo HATA: kural eklenemedi & pause & exit /b 1)

echo [3/4] Python + OpenCV...
set "PY=%HP_PYTHON%"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul ^| findstr /v /i WindowsApps') do if not defined PY set "PY=%%P"
if not defined PY for /f "delims=" %%P in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%P"
if not defined PY (echo HATA: Python yok. & pause & exit /b 1)
"%PY%" -c "import cv2, numpy" || (echo HATA: OpenCV yok: "%PY%" -m pip install opencv-python numpy & pause & exit /b 1)
setx HP_PYTHON "%PY%" >nul
setx HP_KAMERA_BOYUT "%BOYUT%" >nul

echo [4/4] Kamera koprusu baslatiliyor (log: %STAND%\kopru.log)...
taskkill /f /im WindowsCamera.exe >nul 2>&1
wmic process where "CommandLine like '%%kamera_yayin.py%%' or CommandLine like '%%kamera_kopru.py%%'" call terminate >nul 2>&1
start "MemeKopru" /min cmd /c ""%PY%" "%STAND%\kamera_kopru.py" --gonder --bind 192.168.77.2 --port 8090 --kamera 0 --boyut %BOYUT% >> "%STAND%\kopru.log" 2>&1"
timeout /t 5 /nobreak >nul
netstat -an | findstr /c:"192.168.77.2:8090" | findstr LISTENING >nul && (echo TAMAM: kamera 192.168.77.2:8090 yayinda.) || (echo HATA: kopru acilmadi, log: & type "%STAND%\kopru.log")
echo Sonraki gunler: masaustundeki Stant-HP.bat
pause
