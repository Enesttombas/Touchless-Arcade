# HP'ye kamera dosyalarini kablodan verir (USB yerine). YONETICI PowerShell.
# Yalniz 192.168.77.1:8765'te, yalniz 192.168.77.2'ye, yalniz 3 dosya sunar.
# Ctrl+C ile kapat; gecici guvenlik duvari kurali kapanista silinir.
$ErrorActionPreference = 'Stop'
$kok   = Split-Path -Parent $MyInvocation.MyCommand.Path
$dagit = Join-Path $env:TEMP 'memekamera-dagit'
$py    = 'C:\Users\Enes\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$kural = 'MemeKamera-Dagit-8765'

New-Item -ItemType Directory -Force $dagit | Out-Null
Get-ChildItem $dagit -File | Remove-Item -Force
foreach ($f in @("$kok\HP-KAMERA.bat", "$kok\Stant-HP.bat", "$kok\..\prototipler\kamera_kopru.py")) {
    $hedef = Join-Path $dagit (Split-Path -Leaf $f)
    $metin = [IO.File]::ReadAllText((Resolve-Path $f))
    if ($hedef -like '*.bat') { $metin = $metin -replace "(?<!`r)`n", "`r`n" }   # cmd icin CRLF
    [IO.File]::WriteAllText($hedef, $metin, (New-Object Text.UTF8Encoding $false))
}

Remove-NetFirewallRule -Name $kural -ErrorAction SilentlyContinue
New-NetFirewallRule -Name $kural -DisplayName $kural -Direction Inbound -Action Allow -Protocol TCP `
    -LocalPort 8765 -LocalAddress 192.168.77.1 -RemoteAddress 192.168.77.2 -Profile Any | Out-Null
Write-Host "Sunucu acik. HP'de YONETICI cmd'ye yaz:" -ForegroundColor Green
Write-Host "  curl -o C:\stand\HP-KAMERA.bat http://192.168.77.1:8765/HP-KAMERA.bat && C:\stand\HP-KAMERA.bat" -ForegroundColor Yellow
Write-Host "HP 'TAMAM' deyince burada Ctrl+C."
try { & $py -m http.server 8765 --bind 192.168.77.1 --directory $dagit }
finally { Remove-NetFirewallRule -Name $kural -ErrorAction SilentlyContinue; Write-Host 'Gecici kural silindi.' }
