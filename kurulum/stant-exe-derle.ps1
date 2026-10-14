# Stant.exe'yi kurulum\StantLauncher.cs kaynağından derler (.NET Framework 4 csc, ek kurulum gerekmez).
$kok = Split-Path -Parent $PSScriptRoot
$csc = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
& $csc /nologo /target:winexe /optimize+ /out:"$kok\Stant.exe" `
    /r:System.Management.dll /r:System.Windows.Forms.dll "$PSScriptRoot\StantLauncher.cs"
exit $LASTEXITCODE
