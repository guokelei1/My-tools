# Installation script for Campus Network Keep-Alive Service
# Run as Administrator: Right-click PowerShell > "Run as administrator" > paste this script

# Get the script path
$scriptPath = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$keepAliveScript = Join-Path $scriptPath "RuijieKeepAlive.ps1"

Write-Host "================================================"
Write-Host "Campus Network Keep-Alive Service Installer"
Write-Host "================================================"

# Check if running as administrator
$isAdmin = [bool]([Security.Principal.WindowsIdentity]::GetCurrent().Groups -match 'S-1-5-32-544')
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!"
    Write-Host "Please right-click on PowerShell and select 'Run as administrator'"
    Exit 1
}

Write-Host "Installing service..."

# Method 1: Using Task Scheduler (Recommended - more reliable)
Write-Host ""
Write-Host "Setting up Windows Task Scheduler..."

$TaskName = "RuijieKeepAlive"
$TaskExists = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($TaskExists) {
    Write-Host "Found existing task, removing it..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create task trigger (run at startup and every minute as backup)
$trigger = @(
    (New-ScheduledTaskTrigger -AtStartup),
    (New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Days 365))
)

# Create task action (run PowerShell script)
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File `"$keepAliveScript`""

# Create task principal (run with highest privileges, as SYSTEM)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
Register-ScheduledTask -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Description "Monitors and keeps Ruijie Supplicant running for campus network connectivity" `
    -Force | Out-Null

Write-Host "SUCCESS: Task 'RuijieKeepAlive' has been registered!"
Write-Host ""
Write-Host "The service will:"
Write-Host "  • Start automatically when Windows boots"
Write-Host "  • Monitor Ruijie Supplicant every 30 seconds"
Write-Host "  • Automatically restart it if it closes"
Write-Host "  • Log all activities to: $env:APPDATA\RuijieKeepAlive\log.txt"
Write-Host ""
Write-Host "To verify installation, run:"
Write-Host "  Get-ScheduledTask -TaskName RuijieKeepAlive"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  notepad $env:APPDATA\RuijieKeepAlive\log.txt"
Write-Host ""
Write-Host "Installation complete!"
