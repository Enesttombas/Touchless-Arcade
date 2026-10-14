@echo off
rem Cila secimi: her prototipin eski hali (k0) ve yeni kopyalari (k1, k2) sirayla. N/B ile gez, sag altta dosya adi yazar.
cd /d "%~dp0"
if "%KAMERA%"=="" set KAMERA=1
set SECIM=1
set SECILI=p_zaman_klonu__k0,p_zaman_klonu__k1,p_zaman_klonu__k2,p_neon_kilic__k0,p_neon_kilic__k1,p_neon_kilic__k2,p_gulmeme__k0,p_gulmeme__k1,p_gulmeme__k2,p_gorunmez__k0,p_gorunmez__k1,p_maske__k0,p_maske__k1,p_maske__k2
..\app\.venv\Scripts\python.exe gezgin.py
