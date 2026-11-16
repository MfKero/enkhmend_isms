# Run in your normal Windows PowerShell. No Administrator is required.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$ExpectedRemote = 'https://github.com/MfKero/enkhmend_isms.git'
$ActualRemote = (& git remote get-url origin).Trim()
if ($ActualRemote -ne $ExpectedRemote) { throw 'Unexpected Git remote. No push was attempted.' }
& git push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'GitHub push did not complete. Keep the terminal output for troubleshooting.' }
Write-Host 'SUCCESS: Enkhmend ISMS uploaded to https://github.com/MfKero/enkhmend_isms' -ForegroundColor Green
