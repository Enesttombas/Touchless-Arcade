# Ilk acilis kurulumu: oyunun kendine ait tasinabilir Python'unu app\python icine kurar.
# Sisteme hicbir sey yuklemez; app\python klasorunu silmek kurulumu tamamen geri alir.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'  # Invoke-WebRequest ilerleme cubugu indirmeyi cok yavaslatiyor
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$kok = Split-Path -Parent $PSScriptRoot
$hedef = Join-Path $PSScriptRoot 'python'
$gecici = Join-Path $env:TEMP 'touchless-arcade-kurulum'
$pyUrl = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip'
$pipUrl = 'https://bootstrap.pypa.io/get-pip.py'

try {
    New-Item -ItemType Directory -Force -Path $gecici | Out-Null
    if (Test-Path $hedef) { Remove-Item -Recurse -Force $hedef }

    Write-Host '[1/3] Python indiriliyor...'
    $zip = Join-Path $gecici 'python.zip'
    Invoke-WebRequest -Uri $pyUrl -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $hedef -Force
    # Gomulu Python varsayilan olarak site-packages okumaz; paketlerin yuklenebilmesi icin ac.
    Set-Content -Path (Join-Path $hedef 'python311._pth') -Encoding Ascii -Value @(
        'python311.zip', '.', 'Lib\site-packages', 'import site')
    $py = Join-Path $hedef 'python.exe'

    Write-Host '[2/3] Paket yoneticisi kuruluyor...'
    $getPip = Join-Path $gecici 'get-pip.py'
    Invoke-WebRequest -Uri $pipUrl -OutFile $getPip -UseBasicParsing
    & $py $getPip --no-warn-script-location --quiet
    if ($LASTEXITCODE -ne 0) { throw 'pip kurulamadi' }

    Write-Host '[3/3] Oyun paketleri kuruluyor (birkac dakika surebilir)...'
    $gerekenler = Join-Path $kok 'requirements.txt'
    if (Test-Path $gerekenler) {
        & $py -m pip install --no-warn-script-location --quiet -r $gerekenler
    } else {  # klasorde requirements.txt yoksa ayni sabit surumler
        & $py -m pip install --no-warn-script-location --quiet mediapipe==1.0.1 numpy==2.4.6 `
            opencv-contrib-python==5.0.0.93 onnxruntime==1.30.0 pillow==12.3.0
    }
    if ($LASTEXITCODE -ne 0) { throw 'oyun paketleri kurulamadi' }

    Write-Host 'Kurulum tamam.'
    exit 0
}
catch {
    Write-Host ''
    Write-Host "Kurulum basarisiz: $($_.Exception.Message)"
    Write-Host 'Internet baglantisini kontrol edip BASLAT.bat dosyasini tekrar acin.'
    if (Test-Path $hedef) { Remove-Item -Recurse -Force $hedef -ErrorAction SilentlyContinue }
    exit 1
}
