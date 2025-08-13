@echo off
echo 🎓 Academic Research Assistant - Clean Launch
echo ============================================

REM Check if we're in the correct directory
if not exist "src\crew\research_crew.py" (
    echo ❌ Error: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo ✅ Launching error-free Academic Research Assistant...
echo 🌐 Dashboard will open at: http://localhost:8501
echo ⚠️  Press Ctrl+C to stop the dashboard
echo.

REM Set environment variables to reduce warnings
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_THEME_PRIMARY_COLOR=#1e40af
set STREAMLIT_THEME_BACKGROUND_COLOR=#ffffff

REM Start the dashboard with clean output
python -m streamlit run integrated_dashboard.py --server.port 8501 --server.headless false --logger.level error 2>nul

echo.
echo 👋 Academic Research Assistant stopped.
pause
