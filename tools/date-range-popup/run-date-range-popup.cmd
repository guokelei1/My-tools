@echo off
setlocal

set SCRIPT_DIR=%~dp0

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 "%SCRIPT_DIR%date_range_popup.py"
    goto :end
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python "%SCRIPT_DIR%date_range_popup.py"
    goto :end
)

echo Python not found. Please install Python 3 first.
exit /b 1

:end
endlocal
