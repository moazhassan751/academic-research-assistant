@echo off
echo Starting Academic Research Assistant - Integrated Dashboard
echo ========================================================

REM Check if we're in the correct directory
if not exist "src\crew\research_crew.py" (
    echo Error: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Skip virtual environment check since user doesn't want it
echo Using system Python...

REM Check if Streamlit is installed
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Error: Streamlit not found. Installing...
    pip install streamlit plotly pandas aiosqlite
)

REM Check if required packages are available
echo Checking dependencies...
python -c "import aiosqlite; print('✓ aiosqlite available')" 2>nul
if errorlevel 1 (
    echo Installing aiosqlite...
    pip install aiosqlite
)

python -c "import sys; sys.path.insert(0, '.'); from src.crew.research_crew import ResearchCrew; print('✓ Research crew available')" 2>nul
if errorlevel 1 (
    echo Warning: Some research modules may not be available
    echo Please check your installation and dependencies
    echo Installing common missing packages...
    pip install crewai aiosqlite streamlit plotly pandas
)

echo.
echo Starting integrated dashboard...
echo Dashboard will open in your default browser
echo Press Ctrl+C to stop the dashboard
echo.

REM Start the integrated dashboard
python -m streamlit run integrated_dashboard.py --server.port 8501 --server.headless false

pause
