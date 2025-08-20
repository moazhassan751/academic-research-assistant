@echo off
title Academic Research Assistant Launcher
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║               Academic Research Assistant                        ║
echo ║                    Quick Launch (Windows)                        ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo 💡 Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python detected
echo 🚀 Launching Academic Research Assistant...
echo.

python launch.py

pause
