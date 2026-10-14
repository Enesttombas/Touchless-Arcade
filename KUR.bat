@echo off
rem Yeni bilgisayarda bir kez calistir: app\.venv olusturur ve paketleri kurar (internet gerekir).
rem On kosul: Python 3.11 (python.org, "py launcher" secili).
cd /d "%~dp0"
py -3.11 --version >nul 2>&1
if errorlevel 1 (
  python --version 2>nul | findstr /R "3\.11" >nul 2>&1
  if errorlevel 1 (
    echo HATA: Python 3.11 bulunamadi. https://www.python.org/downloads/release/python-3119/ adresinden kurun, "Add python.exe to PATH" ve "py launcher" seceneklerini isaretleyin.
    pause
    exit /b 1
  )
  set "PY_CMD=python"
) else (
  set "PY_CMD=py -3.11"
)

if not exist app\.venv\Scripts\python.exe (
  %PY_CMD% -m venv app\.venv
  if errorlevel 1 (
    echo HATA: app\.venv sanal ortami olusturulamadi. Disk alanini ve yazma izinlerini kontrol edin.
    pause
    exit /b 1
  )
)

app\.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
  echo UYARI: pip guncellemesi atlandi; internet baglantisi sinirli olabilir.
)

app\.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo HATA: Paket kurulumu basarisiz oldu. Internet baglantisini veya PyPI erisimini kontrol edin.
  pause
  exit /b 1
)

rem Model dosyalari kontrolu
if not exist app\modeller\face_landmarker.task (
  echo UYARI: app\modeller\face_landmarker.task dosyasi eksik!
)
if not exist app\modeller\gesture_recognizer.task (
  echo UYARI: app\modeller\gesture_recognizer.task dosyasi eksik!
)
if not exist app\modeller\pose_landmarker_lite.task (
  echo UYARI: app\modeller\pose_landmarker_lite.task dosyasi eksik!
)
if not exist prototipler\modeller\ciz_tanima.onnx (
  echo UYARI: prototipler\modeller\ciz_tanima.onnx modeli eksik!
)

echo Kurulum tamamlandi. BASLAT.bat ile baslatabilirsiniz.
pause
exit /b 0
