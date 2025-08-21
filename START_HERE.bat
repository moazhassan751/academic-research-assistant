@echo off
title Academic ReREM Check if virtual environmeecho ✅ Dependencies verified
echo 🚀 Launching Academic Research Assistant...
echo.
echo 📊 Dashboard will open in your default browser
echo 💻 CLI interface available in terminal
echo 📖 Check README.md for full usage guide
echo.ts
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Virtual environment found - activating...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment detected
    echo 💡 Consider creating one: python -m venv venv
)ssistant v2.1.0 - Windows Launcher
cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                  🎓 Academic Research Assistant v2.1.0                ║
echo ║                      Windows Quick Launcher                           ║
echo ║                                                                        ║
echo ║   AI-Powered Multi-Agent Research System                              ║
echo ║   📚 Literature Discovery • 🤖 AI Analysis • 📝 Draft Generation      ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is available and version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo 💡 Please install Python 3.12+ from https://www.python.org/downloads/
    echo 📖 See README.md for detailed installation instructions
    pause
    exit /b 1
)

REM Get Python version for validation
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% detected

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Virtual environment found - activating...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment detected
    echo � Consider creating one: python -m venv venv
)

REM Check if dependencies are installed
python -c "import streamlit, crewai" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Dependencies not found - installing...
    echo 📦 Installing requirements...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        echo 💡 Try manually: pip install -r requirements.txt
        echo 📖 Or see README.md installation section
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
)

REM Check if database exists, create if needed
if not exist "data\research.db" (
    echo 🗄️  Initializing database...
    if not exist "data" mkdir data
    echo ✅ Database directory ready
)

REM Check for configuration file
if not exist "config.yaml" (
    echo ⚠️  config.yaml not found
    echo 💡 Using default configuration
) else (
    echo ✅ Configuration file found
)

echo ✅ Dependencies verified
echo �🚀 Launching Academic Research Assistant...
echo.
echo 📊 Dashboard will open in your default browser
echo 💻 CLI interface available in terminal
echo 📖 Check README.md for full usage guide
echo.

REM Launch with error handling
python launch.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Launch failed with error code %errorlevel%
    echo 💡 Troubleshooting options:
    echo    1. Check logs\errors.log for detailed error information
    echo    2. Verify Python 3.12+ is installed: python --version
    echo    3. Reinstall dependencies: pip install -r requirements.txt
    echo    4. Try manual launch: python main.py --help
    echo    5. Dashboard only: streamlit run integrated_dashboard.py
    echo    6. See README.md troubleshooting section for more help
    echo.
    echo 🔧 Quick fixes to try:
    echo    - Delete __pycache__ folders and retry
    echo    - Check if all files are in place (main.py, config.yaml)
    echo    - Ensure you're in the project root directory
    echo.
)

pause
