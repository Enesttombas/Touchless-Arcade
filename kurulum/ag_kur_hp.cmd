@echo off
setlocal enabledelayedexpansion

:: Yonetici yetkisi denetimi
fltmc >nul 2>&1
if errorlevel 1 (
    echo HATA: Bu betik yonetici yetkisi ile calistirilmalidir.
    exit /b 1
)

:: Ilk arguman bagdastirici adi, belirtilmemisse varsayilan Ethernet
set "ADAPTER=%~1"
if "%ADAPTER%"=="" set "ADAPTER=Ethernet"

:: Bagdastiricinin varligini dogrula
netsh interface show interface name="%ADAPTER%" >nul 2>&1
if errorlevel 1 (
    echo HATA: Belirtilen ag bagdastiricisi ("%ADAPTER%") bulunamadi.
    exit /b 1
)

:: Statik IP: 192.168.77.2, maske: 255.255.255.0, ag gecidi yok (none)
netsh interface ipv4 set address name="%ADAPTER%" static 192.168.77.2 255.255.255.0 none
if errorlevel 1 (
    echo HATA: Statik IP adresi atanamadi.
    exit /b 1
)

:: Guvenlik duvarini tum profillerde acik tut
netsh advfirewall set allprofiles state on
if errorlevel 1 (
    echo HATA: Guvenlik duvari profilleri etkinlestirilemedi.
    exit /b 1
)

:: Idempotent kural temizligi (yalnizca kendi kural adlarimiz)
netsh advfirewall firewall delete rule name="MemeKameraHPKameraTCP" >nul 2>&1
netsh advfirewall firewall delete rule name="MemeKameraHPKameraUDP" >nul 2>&1

:: Inbound Kamera kurallari (port 8090, local 192.168.77.2, remote 192.168.77.1)
netsh advfirewall firewall add rule name="MemeKameraHPKameraTCP" dir=in action=allow protocol=TCP localport=8090 localip=192.168.77.2 remoteip=192.168.77.1 interfacetype=lan profile=any
if errorlevel 1 (
    echo HATA: MemeKameraHPKameraTCP kurali eklenemedi.
    exit /b 1
)

netsh advfirewall firewall add rule name="MemeKameraHPKameraUDP" dir=in action=allow protocol=UDP localport=8090 localip=192.168.77.2 remoteip=192.168.77.1 interfacetype=lan profile=any
if errorlevel 1 (
    echo HATA: MemeKameraHPKameraUDP kurali eklenemedi.
    exit /b 1
)

echo HP ag ve guvenlik duvari yapilandirmasi basariyla tamamlandi.
exit /b 0
