<#
.SYNOPSIS
    Laptop ag ve guvenlik duvari yapilandirma betigi (MemeKamera - Stant).
.DESCRIPTION
    Bu betik yalnizca belirtilen fiziksel bagdastiriciyi 192.168.77.1/24 (Gateway yok) olarak
    yapilandirir, baglantiyi Private yapar ve Sunshine ile Kamera TCP/UDP portlari icin
    idempotent guvenlik duvari kurallari tanimlar. Diger ag bagdastiricilarina ve kurallara dokunmaz.
.PARAMETER InterfaceAlias
    Yapilandirilacak ag bagdastiricisinin adi. Varsayilan: 'Ethernet'.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$InterfaceAlias = "Ethernet"
)

$ErrorActionPreference = 'Stop'

# Yonetici yetkisi denetimi
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Bu betik yonetici (Administrator) yetkileri ile calistirilmalidir."
}

# Gercek fiziksel ag bagdastiricisini dogrula (HardwareInterface=True ve NdisPhysicalMedium=14 Ethernet)
$adapter = Get-NetAdapter -Name $InterfaceAlias -ErrorAction Stop
if (-not $adapter) {
    throw "Belirtilen ag bagdastiricisi bulunamadi: $InterfaceAlias"
}
if (-not $adapter.HardwareInterface -or [int]$adapter.NdisPhysicalMedium -ne 14) {
    throw "Belirtilen ag bagdastiricisi fiziksel bir Ethernet bagdastiricisi degil: $InterfaceAlias (HardwareInterface=$($adapter.HardwareInterface), NdisPhysicalMedium=$([int]$adapter.NdisPhysicalMedium))"
}

# Yalnizca bu bagdastirici uzerindeki IPv4 adreslerini ve varsayilan rotayi temizle
if ($PSCmdlet.ShouldProcess($InterfaceAlias, "Mevcut IPv4 adreslerini ve varsayilan rotalari kaldir")) {
    Get-NetIPAddress -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue | Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue
    Get-NetRoute -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Remove-NetRoute -Confirm:$false -ErrorAction SilentlyContinue
}

# 192.168.77.1/24 statik IP atamasi (Gateway yok)
if ($PSCmdlet.ShouldProcess($InterfaceAlias, "192.168.77.1/24 (Gateway: NONE) ata")) {
    New-NetIPAddress -InterfaceAlias $InterfaceAlias -IPAddress "192.168.77.1" -PrefixLength 24 -ErrorAction Stop | Out-Null
    Set-NetConnectionProfile -InterfaceAlias $InterfaceAlias -NetworkCategory Private -ErrorAction Stop
}

# Guvenlik duvari profillerini acik tut
if ($PSCmdlet.ShouldProcess("FirewallProfiles", "Tum profilleri etkinlestir")) {
    Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True -ErrorAction Stop
}

# Idempotent kural temizligi: Yalnizca kendi kural grubumuzu temizle
$GroupName = "MemeKamera-Stant"
if ($PSCmdlet.ShouldProcess($GroupName, "Onceki guvenlik duvari kurallarini temizle")) {
    Remove-NetFirewallRule -DisplayGroup $GroupName -ErrorAction SilentlyContinue
}

# Sunshine ve Kamera kurallari listesi
$rules = @(
    @{
        Name = "MemeKamera-Sunshine-TCP"
        DisplayName = "MemeKamera Sunshine TCP"
        Protocol = "TCP"
        LocalPort = @("47984", "47989", "47990", "48010")
    },
    @{
        Name = "MemeKamera-Sunshine-UDP"
        DisplayName = "MemeKamera Sunshine UDP"
        Protocol = "UDP"
        LocalPort = @("47998", "47999", "48000", "48002", "48010")
    },
    @{
        Name = "MemeKamera-Kamera-TCP"
        DisplayName = "MemeKamera Kopru TCP"
        Protocol = "TCP"
        LocalPort = @("8090")
    },
    @{
        Name = "MemeKamera-Kamera-UDP"
        DisplayName = "MemeKamera Kopru UDP"
        Protocol = "UDP"
        LocalPort = @("8090")
    }
)

foreach ($r in $rules) {
    if ($PSCmdlet.ShouldProcess($r.DisplayName, "Guvenlik duvari kuralini ekle")) {
        New-NetFirewallRule `
            -Name $r.Name `
            -DisplayName $r.DisplayName `
            -Group $GroupName `
            -Direction Inbound `
            -Action Allow `
            -Protocol $r.Protocol `
            -LocalPort $r.LocalPort `
            -LocalAddress "192.168.77.1" `
            -RemoteAddress "192.168.77.2" `
            -InterfaceAlias $InterfaceAlias `
            -Profile Private `
            -Enabled True `
            -ErrorAction Stop | Out-Null
    }
}

if ($PSCmdlet.ShouldProcess("Laptop", "Kurulum tamamlama bildirimi")) {
    Write-Host "Laptop ag ve guvenlik duvari yapilandirmasi basariyla tamamlandi."
} else {
    Write-Host "Laptop ag ve guvenlik duvari yapilandirmasi onizlemesi (WhatIf) tamamlandi."
}
