$ErrorActionPreference = 'Stop'

$profilePath = $PROFILE
$profileDir = Split-Path -Parent $profilePath

if (-not (Test-Path -LiteralPath $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

if (-not (Test-Path -LiteralPath $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

$shortcutCdBlock = @'
# >>> shortcut-cd >>>
function global:__ShortcutCd {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$PathParts
    )

    if (-not $PathParts -or $PathParts.Count -eq 0) {
        Microsoft.PowerShell.Management\Set-Location
        return
    }

    $rawPath = $PathParts -join ' '

    try {
        Microsoft.PowerShell.Management\Set-Location -Path $rawPath -ErrorAction Stop
        return
    } catch {}

    $candidatePaths = @()

    if ([System.IO.Path]::GetExtension($rawPath)) {
        $candidatePaths += $rawPath
    } else {
        $candidatePaths += "$rawPath.lnk"
        $candidatePaths += "$rawPath.link"
    }

    $wshShell = $null

    foreach ($candidatePath in $candidatePaths) {
        try {
            $item = Get-Item -LiteralPath $candidatePath -ErrorAction Stop

            if ($item.PSIsContainer) {
                Microsoft.PowerShell.Management\Set-Location -LiteralPath $item.FullName
                return
            }

            if ($item.Extension -in '.lnk', '.link') {
                if (-not $wshShell) {
                    $wshShell = New-Object -ComObject WScript.Shell
                }

                $resolvedTarget = $wshShell.CreateShortcut($item.FullName).TargetPath

                if ($resolvedTarget -and (Test-Path -LiteralPath $resolvedTarget -PathType Container)) {
                    Microsoft.PowerShell.Management\Set-Location -LiteralPath $resolvedTarget
                    return
                }
            }
        } catch {}
    }

    Microsoft.PowerShell.Management\Set-Location -Path $rawPath
}

Set-Alias -Name cd -Value __ShortcutCd -Scope Global -Option AllScope -Force
Set-Alias -Name sl -Value __ShortcutCd -Scope Global -Option AllScope -Force
Set-Alias -Name chdir -Value __ShortcutCd -Scope Global -Option AllScope -Force
# <<< shortcut-cd <<<
'@

$existingContent = if (Test-Path -LiteralPath $profilePath) {
    [string](Get-Content -LiteralPath $profilePath -Raw)
} else {
    ''
}

$cleanContent = [regex]::Replace(
    $existingContent,
    '(?s)# >>> shortcut-cd >>>.*?# <<< shortcut-cd <<<\r?\n?',
    ''
)

$newContent = ($cleanContent.TrimEnd() + "`r`n`r`n" + $shortcutCdBlock.Trim() + "`r`n")
Set-Content -LiteralPath $profilePath -Value $newContent -Encoding UTF8

. $PROFILE

Write-Host 'shortcut-cd installed'
Write-Host "Profile: $PROFILE"
Write-Host 'Usage: cd .\codex'



