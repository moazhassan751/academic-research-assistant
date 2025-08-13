#!/bin/bash

echo "🎓 Academic Research Assistant - Clean Launch"
echo "============================================"

# Check if we're in the correct directory
if [ ! -f "src/crew/research_crew.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "✅ Launching error-free Academic Research Assistant..."
echo "🌐 Dashboard will open at: http://localhost:8501"
echo "⚠️  Press Ctrl+C to stop the dashboard"
echo ""

# Set environment variables to reduce warnings
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_THEME_PRIMARY_COLOR="#1e40af"
export STREAMLIT_THEME_BACKGROUND_COLOR="#ffffff"

# Start the dashboard with clean output
python -m streamlit run integrated_dashboard.py --server.port 8501 --server.headless false --logger.level error 2>/dev/null

echo ""
echo "👋 Academic Research Assistant stopped."
