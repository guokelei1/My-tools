$ErrorActionPreference = 'Stop'

$profilePath = $PROFILE

if (Test-Path -LiteralPath $profilePath) {
    $existingContent = [string](Get-Content -LiteralPath $profilePath -Raw)
    $cleanContent = [regex]::Replace(
        $existingContent,
        '(?s)# >>> shortcut-cd >>>.*?# <<< shortcut-cd <<<\r?\n?',
        ''
    )

    Set-Content -LiteralPath $profilePath -Value $cleanContent -Encoding UTF8
}

if (Test-Path Alias:cd) {
    Remove-Item Alias:cd -Force -ErrorAction SilentlyContinue
}
if (Test-Path Alias:sl) {
    Remove-Item Alias:sl -Force -ErrorAction SilentlyContinue
}
if (Test-Path Alias:chdir) {
    Remove-Item Alias:chdir -Force -ErrorAction SilentlyContinue
}
if (Test-Path Function:\__ShortcutCd) {
    Remove-Item Function:\__ShortcutCd -Force -ErrorAction SilentlyContinue
}

Set-Alias -Name cd -Value Set-Location -Scope Global -Option AllScope -Force
Set-Alias -Name sl -Value Set-Location -Scope Global -Option AllScope -Force
Set-Alias -Name chdir -Value Set-Location -Scope Global -Option AllScope -Force

. $PROFILE

Write-Host 'shortcut-cd uninstalled'
Write-Host "Profile: $PROFILE"




