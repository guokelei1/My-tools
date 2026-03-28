# Uninstallation script for Campus Network Keep-Alive Service
# Run as Administrator if you want to remove the service

Write-Host "================================================"
Write-Host "Campus Network Keep-Alive Service Uninstaller"
Write-Host "================================================"

# Check if running as administrator
$isAdmin = [bool]([Security.Principal.WindowsIdentity]::GetCurrent().Groups -match 'S-1-5-32-544')
if (-not $isAdmin) {
    Write-Host "WARNING: This script should be run as Administrator!"
}

Write-Host ""
Write-Host "Removing scheduled task 'RuijieKeepAlive'..."

$TaskName = "RuijieKeepAlive"
$TaskExists = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($TaskExists) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "SUCCESS: Task has been removed!"
} else {
    Write-Host "INFO: Task 'RuijieKeepAlive' not found (already uninstalled?)"
}

Write-Host ""
Write-Host "The service has been uninstalled."
Write-Host "Ruijie Supplicant will no longer be monitored automatically."
