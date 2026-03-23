$ErrorActionPreference = 'Stop'

$profilePath = $PROFILE
$profileDir = Split-Path -Parent $profilePath

if (-not (Test-Path -LiteralPath $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

if (-not (Test-Path -LiteralPath $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

$proxyBlock = @'
# >>> proxy-toggle >>>
function global:proxy {
    $proxyUrl = 'http://127.0.0.1:7890'
    $httpEnabled = $env:HTTP_PROXY -eq $proxyUrl
    $httpsEnabled = $env:HTTPS_PROXY -eq $proxyUrl

    if ($httpEnabled -and $httpsEnabled) {
        Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
        Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
        Write-Host 'proxy disabled'
        return
    }

    $env:HTTP_PROXY = $proxyUrl
    $env:HTTPS_PROXY = $proxyUrl

    Write-Host "proxy enabled -> $proxyUrl"
}
# <<< proxy-toggle <<<
'@

$existingContent = if (Test-Path -LiteralPath $profilePath) {
    [string](Get-Content -LiteralPath $profilePath -Raw)
} else {
    ''
}

$cleanContent = [regex]::Replace(
    $existingContent,
    '(?s)# >>> proxy-toggle >>>.*?# <<< proxy-toggle <<<\r?\n?',
    ''
)

$trimmedContent = $cleanContent.TrimEnd()

if ([string]::IsNullOrWhiteSpace($trimmedContent)) {
    $newContent = $proxyBlock.Trim() + "`r`n"
} else {
    $newContent = $trimmedContent + "`r`n`r`n" + $proxyBlock.Trim() + "`r`n"
}

Set-Content -LiteralPath $profilePath -Value $newContent -Encoding UTF8

. $PROFILE

Write-Host 'proxy-toggle installed'
Write-Host "Profile: $PROFILE"
Write-Host 'Usage: proxy'

