@echo off
REM IPO Backtest Terminal Launcher for Windows

REM Get the directory of this script
set DIR=%~dp0

REM Change to project directory
cd /d "%DIR%"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements if needed
echo Checking dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt 2>nul
pip install -q -r requirements_app.txt 2>nul

REM ASCII art header
echo.
echo ============================================
echo        IPO BACKTEST TERMINAL v1.0
echo      Modern Finance Analytics Platform
echo ============================================
echo.

REM Run the application
python run_app.py

pause