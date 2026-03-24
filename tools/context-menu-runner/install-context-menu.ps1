$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$menuRoot = Join-Path $HOME 'menu'
$installRoot = Join-Path $menuRoot 'context-menu-runner'
$verbName = 'MyTools.ContextMenuRunner'
$menuText = 'git 一键push'

$requiredPaths = @(
    (Join-Path $scriptRoot 'launcher\run-context.cmd'),
    (Join-Path $scriptRoot 'app\__init__.py'),
    (Join-Path $scriptRoot 'app\main.py'),
    (Join-Path $scriptRoot 'app\context.py'),
    (Join-Path $scriptRoot 'app\executor.py'),
    (Join-Path $scriptRoot 'app\backends.py'),
    (Join-Path $scriptRoot 'app\config.py'),
    (Join-Path $scriptRoot 'actions\default_action.py')
)

foreach ($requiredPath in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required file not found: $requiredPath"
    }
}

New-Item -ItemType Directory -Path $menuRoot -Force | Out-Null
New-Item -ItemType Directory -Path $installRoot -Force | Out-Null

foreach ($folderName in @('launcher', 'app', 'actions')) {
    $sourcePath = Join-Path $scriptRoot $folderName
    $targetPath = Join-Path $installRoot $folderName

    if (Test-Path -LiteralPath $targetPath) {
        Remove-Item -LiteralPath $targetPath -Recurse -Force
    }

    Copy-Item -LiteralPath $sourcePath -Destination $installRoot -Recurse -Force
}

$logsPath = Join-Path $installRoot 'logs'
New-Item -ItemType Directory -Path $logsPath -Force | Out-Null

$metadata = [ordered]@{
    source_root = $scriptRoot
    install_root = $installRoot
    launcher_path = (Join-Path $installRoot 'launcher\run-context.cmd')
    installed_at = (Get-Date).ToString('o')
}

$metadataPath = Join-Path $installRoot 'install-metadata.json'
$metadata | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $metadataPath -Encoding UTF8

$launcherPath = Join-Path $installRoot 'launcher\run-context.cmd'

$directoryKey = "HKCU:\Software\Classes\Directory\shell\$verbName"
$directoryCommandKey = Join-Path $directoryKey 'command'
$backgroundKey = "HKCU:\Software\Classes\Directory\Background\shell\$verbName"
$backgroundCommandKey = Join-Path $backgroundKey 'command'

$directoryCommand = "`"$launcherPath`" --mode directory --target `"%1`""
$backgroundCommand = "`"$launcherPath`" --mode background --target `"%V`""

New-Item -Path $directoryKey -Force | Out-Null
Set-Item -Path $directoryKey -Value $menuText
New-ItemProperty -Path $directoryKey -Name 'Icon' -Value $launcherPath -PropertyType String -Force | Out-Null

New-Item -Path $directoryCommandKey -Force | Out-Null
Set-Item -Path $directoryCommandKey -Value $directoryCommand

New-Item -Path $backgroundKey -Force | Out-Null
Set-Item -Path $backgroundKey -Value $menuText
New-ItemProperty -Path $backgroundKey -Name 'Icon' -Value $launcherPath -PropertyType String -Force | Out-Null

New-Item -Path $backgroundCommandKey -Force | Out-Null
Set-Item -Path $backgroundCommandKey -Value $backgroundCommand

Write-Host 'context-menu-runner installed'
Write-Host "Source root: $scriptRoot"
Write-Host "Install root: $installRoot"
Write-Host "Launcher: $launcherPath"
Write-Host "Directory verb: $directoryKey"
Write-Host "Background verb: $backgroundKey"
Write-Host 'Use uninstall-context-menu.ps1 to remove the registry entries.'
