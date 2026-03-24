param(
    [switch]$RemoveInstalledFiles
)

$ErrorActionPreference = 'Stop'

$installRoot = Join-Path (Join-Path $HOME 'menu') 'context-menu-runner'
$verbName = 'MyTools.ContextMenuRunner'

$registryKeys = @(
    "HKCU:\Software\Classes\Directory\shell\$verbName",
    "HKCU:\Software\Classes\Directory\Background\shell\$verbName"
)

foreach ($registryKey in $registryKeys) {
    if (Test-Path -LiteralPath $registryKey) {
        Remove-Item -LiteralPath $registryKey -Recurse -Force
        Write-Host "Removed registry key: $registryKey"
    } else {
        Write-Host "Registry key not found: $registryKey"
    }
}

if ($RemoveInstalledFiles) {
    if (Test-Path -LiteralPath $installRoot) {
        Remove-Item -LiteralPath $installRoot -Recurse -Force
        Write-Host "Removed install root: $installRoot"
    } else {
        Write-Host "Install root not found: $installRoot"
    }
} else {
    Write-Host "Install root preserved: $installRoot"
    Write-Host 'Run with -RemoveInstalledFiles to delete the installed runtime files.'
}

Write-Host 'context-menu-runner uninstalled'
