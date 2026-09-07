[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Python,
    [string]$GuardianHome = (Join-Path $env:USERPROFILE '.guardian-native'),
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' })
)
$ErrorActionPreference = 'Stop'
$Bundle = Split-Path -Parent $PSScriptRoot
$Manifest = Join-Path $Bundle 'SHA256SUMS.txt'
if (-not (Test-Path $Manifest)) { throw 'Use the complete release bundle with SHA256SUMS.txt.' }
foreach ($Line in Get-Content $Manifest) {
    if ($Line -match '^([0-9a-fA-F]{64})  (.+)$') {
        $Expected = $Matches[1]
        $Relative = $Matches[2]
        if ([IO.Path]::IsPathRooted($Relative) -or $Relative.Contains('..')) { throw 'Invalid manifest path.' }
        $File = Join-Path $Bundle $Relative
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $File).Hash -ne $Expected) { throw "Checksum mismatch: $Relative" }
    } else { throw 'Malformed checksum manifest.' }
}
& $Python -c 'import sys; assert sys.version_info >= (3,11), "Guardian runtime needs Python 3.11+"'
if ($LASTEXITCODE -ne 0) { throw 'Select an installed Python 3.11+ interpreter.' }
$Runtime = Join-Path $GuardianHome 'venv'
if (-not (Test-Path (Join-Path $Runtime 'Scripts/python.exe'))) {
    & $Python -m venv $Runtime
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create a standard-user virtual environment.' }
}
$GuardianPython = Join-Path $Runtime 'Scripts/python.exe'
$Wheels = @(Get-ChildItem -LiteralPath (Join-Path $Bundle 'dist') -Filter 'guardian_native-*.whl')
if ($Wheels.Count -ne 1) { throw 'Expected exactly one Guardian wheel.' }
& $GuardianPython -m pip install --no-index --no-deps --no-cache-dir --disable-pip-version-check --force-reinstall $Wheels[0].FullName
if ($LASTEXITCODE -ne 0) { throw 'Offline wheel installation failed.' }
& $GuardianPython -I -m guardian_next.cli --home $GuardianHome install --codex-home $CodexHome
if ($LASTEXITCODE -ne 0) { throw 'Personal hook installation failed; inspect the reported preserved configuration.' }
Write-Output "Installed. Restart Codex. Next: use docs/LAPTOP-START.md to register and validate the actual team environment. Runtime: $GuardianPython"
