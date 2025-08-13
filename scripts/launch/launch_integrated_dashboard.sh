#!/bin/bash

echo "Starting Academic Research Assistant - Integrated Dashboard"
echo "========================================================"

# Check if we're in the correct directory
if [ ! -f "src/crew/research_crew.py" ]; then
    echo "Error: Please run this script from the project root directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Check if virtual environment exists and activate it
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Warning: Virtual environment not found"
    echo "Using system Python..."
fi

# Check if Streamlit is installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "Error: Streamlit not found. Installing..."
    pip install streamlit
fi

# Check if required packages are available
echo "Checking dependencies..."
if python -c "import sys; sys.path.insert(0, '.'); from src.crew.research_crew import ResearchCrew; print('✓ Research crew available')" 2>/dev/null; then
    echo "✓ All research modules available"
else
    echo "Warning: Some research modules may not be available"
    echo "Please check your installation and dependencies"
fi

echo ""
echo "Starting integrated dashboard..."
echo "Dashboard will open in your default browser"
echo "Press Ctrl+C to stop the dashboard"
echo ""

# Start the integrated dashboard
streamlit run integrated_dashboard.py --server.port 8501 --server.headless false
