<#
.SYNOPSIS
    Laptop tarafi gunluk stant baslatici betigi (MemeKamera - Stant).
.DESCRIPTION
    Yonetici PowerShell ile calistirilir. Sirasiyla:
    1) Ethernet IP (192.168.77.1) ve kablo baglantisini denetler/kurar.
    2) Sunshine konfigurasyonunu (nvenc ve 1080p60) yedekleyerek gunceller.
    3) SunshineService hizmetini baslatir veya yeniden baslatir.
    4) HP karsi makinedeki kamera koprusunun (192.168.77.2:8090) hazir olmasini bekler.
    5) Stant.exe uygulamasini tam ekran ve kamera degiskenleriyle baslatir.
.PARAMETER InterfaceAlias
    Yapilandirilacak ag bagdastiricisinin adi. Varsayilan: 'Ethernet'.
.PARAMETER KameraBekleme
    Verilirse 4. adimdaki kamera koprusu port beklemesi atlanir.
#>
[CmdletBinding()]
param(
    [string]$InterfaceAlias = 'Ethernet',
    [switch]$KameraBekleme
)

$ErrorActionPreference = 'Stop'
$kok = Split-Path -Parent $PSScriptRoot

# 0) Yonetici yetkisi denetimi
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Bu betik yonetici (Administrator) yetkileri ile calistirilmalidir."
}

# 1) Ag ve kablo kontrolu
Write-Host "[1/5] Ethernet ag ayarlari ve kablo baglantisi kontrol ediliyor..."
$mevcutIp = Get-NetIPAddress -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -eq '192.168.77.1' }

if (-not $mevcutIp) {
    $agKurBetik = Join-Path $PSScriptRoot 'ag_kur_laptop.ps1'
    & $agKurBetik -InterfaceAlias $InterfaceAlias
}

$adapter = Get-NetAdapter -Name $InterfaceAlias -ErrorAction Stop
if ($adapter.Status -ne 'Up') {
    throw 'Ethernet kablosu bagli degil'
}

# 2) Sunshine yapilandirmasi
Write-Host "[2/5] Sunshine yapilandirmasi (sunshine.conf) guncelleniyor..."
$conf = 'C:\Program Files\Sunshine\config\sunshine.conf'
$yedek = "$conf.stant-yedek"

if (-not (Test-Path -LiteralPath $conf)) {
    throw "Sunshine yapilandirma dosyasi bulunamadi: $conf"
}

if (-not (Test-Path -LiteralPath $yedek)) {
    Copy-Item -LiteralPath $conf -Destination $yedek -ErrorAction Stop
}

$satirlar = [System.Collections.Generic.List[string]]::new()
$mevcutIcerik = [System.IO.File]::ReadAllLines($conf, [System.Text.Encoding]::UTF8)
foreach ($s in $mevcutIcerik) {
    $satirlar.Add($s)
}

$ayarlar = [ordered]@{
    'encoder'                = 'nvenc'
    'nvenc_preset'           = '1'
    'nvenc_twopass'          = 'disabled'
    'dd_resolution_option'   = 'manual'
    'dd_manual_resolution'   = '1920x1080'
    'dd_refresh_rate_option' = 'manual'
    'dd_manual_refresh_rate' = '60'
}

foreach ($anahtar in $ayarlar.Keys) {
    $deger = $ayarlar[$anahtar]
    $yeniSatir = "$anahtar = $deger"
    $desen = "^\s*" + [regex]::Escape($anahtar) + "\s*="
    $bulundu = $false

    for ($i = 0; $i -lt $satirlar.Count; $i++) {
        if ($satirlar[$i] -match $desen) {
            $satirlar[$i] = $yeniSatir
            $bulundu = $true
            break
        }
    }

    if (-not $bulundu) {
        $satirlar.Add($yeniSatir)
    }
}

$utf8Bomsuz = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($conf, $satirlar.ToArray(), $utf8Bomsuz)

# 3) Sunshine servisi
Write-Host "[3/5] SunshineService hizmeti baslatiliyor / yeniden baslatiliyor..."
$servis = Get-Service -Name 'SunshineService' -ErrorAction Stop
if ($servis.Status -eq 'Running') {
    Restart-Service -Name 'SunshineService' -ErrorAction Stop
} else {
    Start-Service -Name 'SunshineService' -ErrorAction Stop
}
Write-Host "Sunshine eslestirme (PIN) arayuzu: https://localhost:47990"

# 4) Kamera koprusu bekleme
if ($KameraBekleme) {
    Write-Host "[4/5] Kamera koprusu bekleme adimi atlandi (-KameraBekleme)."
} else {
    Write-Host "[4/5] HP kamera koprusu (192.168.77.2:8090) bekleniyor (en fazla 90 sn)..."
    $basarili = $false
    $zamanAsimiSaniye = 90
    $aralikSaniye = 3
    $gecenSaniye = 0

    while ($gecenSaniye -lt $zamanAsimiSaniye) {
        $baglanti =Test-NetConnection -ComputerName '192.168.77.2' -Port 8090 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($baglanti) {
            $basarili = $true
            break
        }
        Start-Sleep -Seconds $aralikSaniye
        $gecenSaniye += $aralikSaniye
    }

    if (-not $basarili) {
        throw "192.168.77.2:8090 uzerindeki kamera koprusune 90 saniye icinde ulasilamadi. Lutfen HP bilgisayardaki C:\stand\kopru.log dosyasini kontrol edin."
    }
}

# 5) Stant.exe baslatma
Write-Host "[5/5] Stant.exe baslatiliyor..."
$env:KAMERA = 'tcp://192.168.77.2:8090'
$env:TAM_EKRAN = '1'
$stantExe = Join-Path $kok 'Stant.exe'
Start-Process -FilePath $stantExe -WorkingDirectory $kok
