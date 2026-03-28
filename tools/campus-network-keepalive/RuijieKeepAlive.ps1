# Campus Network Keep-Alive Monitor
# This script keeps Ruijie Supplicant running continuously
# It checks every 30 seconds and restarts if needed

$RuijieExePath = "C:\Program Files\Ruijie Networks\Ruijie Supplicant\RuijieSupplicant.exe"
$LogFile = "$env:APPDATA\RuijieKeepAlive\log.txt"
$LogDir = Split-Path $LogFile

# Create log directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Add-Content -Path $LogFile -Value $logMessage
    Write-Host $logMessage
}

Write-Log "=== Campus Network Keep-Alive Service Started ==="

# Main monitoring loop
$lastStartTime = Get-Date
$startInterval = 3600  # 1 hour in seconds

while ($true) {
    try {
        $currentTime = Get-Date
        $timeSinceLastStart = ($currentTime - $lastStartTime).TotalSeconds

        # Check if Ruijie Supplicant is running
        $ruijieProcess = Get-Process -Name "RuijieSupplicant" -ErrorAction SilentlyContinue

        # Condition 1: Process not found - start it immediately
        if ($null -eq $ruijieProcess) {
            Write-Log "WARNING: RuijieSupplicant not running! Starting it now..."

            if (Test-Path $RuijieExePath) {
                Start-Process -FilePath $RuijieExePath
                Write-Log "SUCCESS: RuijieSupplicant has been started"
                $lastStartTime = $currentTime
            } else {
                Write-Log "ERROR: RuijieSupplicant.exe not found at $RuijieExePath"
            }
        }
        # Condition 2: Every 1 hour, start it again (even if already running)
        elseif ($timeSinceLastStart -ge $startInterval) {
            Write-Log "INFO: 1 hour reached! Starting RuijieSupplicant again to keep connection active..."

            if (Test-Path $RuijieExePath) {
                Start-Process -FilePath $RuijieExePath
                Write-Log "SUCCESS: RuijieSupplicant has been started (connection kept active)"
                $lastStartTime = $currentTime
            } else {
                Write-Log "ERROR: RuijieSupplicant.exe not found at $RuijieExePath"
            }
        }
        else {
            # Normal status check
            $timeUntilNextStart = [math]::Round($startInterval - $timeSinceLastStart, 0)
            Write-Log "OK: RuijieSupplicant is running (PID: $($ruijieProcess.Id)) - Next periodic start in $timeUntilNextStart seconds"
        }
    }
    catch {
        Write-Log "ERROR: $($_.Exception.Message)"
    }

    # Check every 30 seconds
    Start-Sleep -Seconds 30
}
