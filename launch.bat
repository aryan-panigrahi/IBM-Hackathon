@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: The Governance Tribunal — Windows Launcher
:: Double-click this file in Explorer to launch the Tribunal.
:: ─────────────────────────────────────────────────────────────────────────────

:: Move to the directory containing this script
cd /d "%~dp0"

:: Enable coloured output in Windows 10+
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  X  Python not found.
    echo     Download from: https://www.python.org/downloads/
    echo     Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

:: Launch the shared Python launcher
python launch.py

pause
