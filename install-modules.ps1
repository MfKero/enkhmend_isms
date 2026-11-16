# Run in Windows PowerShell as Administrator.
# Installs only OCA Helpdesk and Audit Log into the existing enkhmend_isms DB.
$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$OdooRoot = 'C:\Program Files\Odoo 19.0.20261116'
$ConfigFile = Join-Path $OdooRoot 'server\odoo.conf'
$PythonExe = Join-Path $OdooRoot 'python\python.exe'
$OdooBin = Join-Path $OdooRoot 'server\odoo-bin'
$AddonsFolder = Join-Path $ProjectRoot 'addons'
$Database = 'enkhmend_isms'
$LogFile = Join-Path $ProjectRoot 'module-install.log'
$BackupFolder = Join-Path $OdooRoot 'server'

try {
    $Principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Administrator required. Open Windows PowerShell as Administrator and run this file.'
    }
    foreach ($ModuleName in @('helpdesk_mgmt','auditlog')) {
        $Manifest = Join-Path $AddonsFolder ($ModuleName + '\__manifest__.py')
        if (-not (Test-Path -LiteralPath $Manifest)) { throw "Missing module: $ModuleName" }
    }
    # Match the verified application service exactly; '*odoo*' also matches PostgreSQL_For_Odoo.
    $OdooService = Get-Service -Name 'odoo-server-19.0' -ErrorAction Stop
    $OriginalConfig = [IO.File]::ReadAllText($ConfigFile)
    $AddonLine = [regex]::Match($OriginalConfig, '(?m)^addons_path\s*=\s*([^\r\n]*)')
    if (-not $AddonLine.Success) { throw 'addons_path was not found. No configuration has been changed.' }
    $BackupFile = Join-Path $BackupFolder ('odoo.conf.before-enkhmend-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.bak')
    Copy-Item -LiteralPath $ConfigFile -Destination $BackupFile
    $ExistingPaths = @($AddonLine.Groups[1].Value.Split(',') | ForEach-Object { $_.Trim() })
    $UpdatedConfig = $OriginalConfig
    if ($ExistingPaths -notcontains $AddonsFolder) {
        $NewLine = 'addons_path = ' + (($ExistingPaths + $AddonsFolder) -join ',')
        $UpdatedConfig = $OriginalConfig.Substring(0, $AddonLine.Index) + $NewLine + $OriginalConfig.Substring($AddonLine.Index + $AddonLine.Length)
    }
    [IO.File]::WriteAllText($ConfigFile, $UpdatedConfig, (New-Object Text.UTF8Encoding($false)))
    Write-Host "Backup: $BackupFile"
    Write-Host "Stopping $($OdooService.Name) temporarily..."
    $WasRunning = $OdooService.Status -eq 'Running'
    try {
        if ($WasRunning) {
            Stop-Service -InputObject $OdooService
            $OdooService.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(60))
        }
        Write-Host 'Installing helpdesk_mgmt and auditlog into enkhmend_isms...'
        & $PythonExe $OdooBin -c $ConfigFile -d $Database -i 'helpdesk_mgmt,auditlog' --without-demo --stop-after-init --no-http --logfile $LogFile
        if ($LASTEXITCODE -ne 0) { throw "Odoo installation failed. Check $LogFile" }
    } finally {
        if ($WasRunning) { Start-Service -Name $OdooService.Name }
    }
    Write-Host ''
    Write-Host 'SUCCESS: Helpdesk and Audit Log installed. Open http://localhost:8069 and refresh.' -ForegroundColor Green
    Write-Host "Installation log: $LogFile"
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
