@echo off
REM Weekly Scorecard Dashboard - one-click refresh (Windows)
REM Double-click this file in Explorer to rebuild the dashboard from your archive.

setlocal
cd /d "%~dp0"

echo ================================================
echo   Weekly Scorecard - Dashboard Refresh
echo ================================================
echo.

REM Find a Python interpreter
set PY=
where python >nul 2>&1 && set PY=python
if "%PY%"=="" (
    where py >nul 2>&1 && set PY=py
)
if "%PY%"=="" (
    echo ERROR: no Python 3 found on PATH.
    echo Install Python from https://www.python.org/downloads/ and check "Add Python to PATH".
    pause
    exit /b 1
)

REM Ensure required libraries
%PY% -c "import pandas, numpy, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo Installing required Python packages (one-time setup)...
    %PY% -m pip install --user pandas numpy openpyxl --quiet
    if errorlevel 1 (
        echo pip install failed. Try running manually: %PY% -m pip install pandas numpy openpyxl
        pause
        exit /b 1
    )
)

%PY% .scorecard\refresh.py
if errorlevel 1 (
    echo.
    echo Refresh failed. See error above.
    pause
    exit /b 1
)

echo.
echo Dashboard rebuilt. Opening Signal_Dashboard.xlsx...
start "" "Signal_Dashboard.xlsx"

echo.
pause
