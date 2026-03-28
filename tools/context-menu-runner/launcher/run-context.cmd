@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "INSTALL_ROOT=%%~fI"
set "MAIN_PY=%INSTALL_ROOT%\app\main.py"
set "VENV_PYTHON=%INSTALL_ROOT%\.venv\Scripts\python.exe"
set "EXIT_CODE=1"

if not exist "%MAIN_PY%" (
    echo context-menu-runner error: main.py not found.
    echo Expected: %MAIN_PY%
    echo Press any key to close this window.
    pause >nul
    exit /b 1
)

if exist "%VENV_PYTHON%" (
    goto run_venv
)

where py.exe >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        goto run_py
    )
)

where python.exe >nul 2>nul
if not errorlevel 1 (
    goto run_python
)

echo context-menu-runner error: no Python interpreter found.
echo Tried:
echo   %VENV_PYTHON%
echo   py -3
echo   python
set "EXIT_CODE=1"
goto finish

:run_venv
"%VENV_PYTHON%" "%MAIN_PY%" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto finish

:run_py
py -3 "%MAIN_PY%" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto finish

:run_python
python "%MAIN_PY%" %*
set "EXIT_CODE=%ERRORLEVEL%"

:finish
if "%EXIT_CODE%"=="0" (
    powershell.exe -NoProfile -Command "Start-Sleep -Seconds 5" >nul 2>nul
)

if not "%EXIT_CODE%"=="0" (
    echo.
    echo context-menu-runner exited with code %EXIT_CODE%.
    echo Install root: %INSTALL_ROOT%
    echo Press any key to close this window.
    pause >nul
)

exit /b %EXIT_CODE%
