[CmdletBinding()]
param([string]$GuardianHome = (Join-Path $env:USERPROFILE '.guardian-native'))
$ErrorActionPreference = 'Stop'
$GuardianPython = Join-Path $GuardianHome 'venv/Scripts/python.exe'
& $GuardianPython -I -m guardian_next.cli --home $GuardianHome uninstall
if ($LASTEXITCODE -ne 0) { throw 'Removal needs inspection; modified files and evidence have been preserved.' }
Write-Output 'Personal integration removed. Restart Codex. Runtime, backups and task evidence remain for inspection.'
