$ErrorActionPreference = 'Stop'

$profilePath = $PROFILE
$proxyUrl = 'http://127.0.0.1:7890'

if (Test-Path -LiteralPath $profilePath) {
    $existingContent = [string](Get-Content -LiteralPath $profilePath -Raw)
    $cleanContent = [regex]::Replace(
        $existingContent,
        '(?s)# >>> proxy-toggle >>>.*?# <<< proxy-toggle <<<\r?\n?',
        ''
    )

    Set-Content -LiteralPath $profilePath -Value $cleanContent -Encoding UTF8
}

if (Test-Path Function:\proxy) {
    Remove-Item Function:\proxy -Force -ErrorAction SilentlyContinue
}

if ($env:HTTP_PROXY -eq $proxyUrl) {
    Remove-Item Env:HTTP_PROXY -Force -ErrorAction SilentlyContinue
}

if ($env:HTTPS_PROXY -eq $proxyUrl) {
    Remove-Item Env:HTTPS_PROXY -Force -ErrorAction SilentlyContinue
}

. $PROFILE

Write-Host 'proxy-toggle uninstalled'
Write-Host "Profile: $PROFILE"

