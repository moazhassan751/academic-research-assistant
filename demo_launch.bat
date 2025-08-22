@echo off
echo Starting OPTIMIZED Academic Research Assistant Demo...
echo ===============================================

REM Set demo environment variables
set STREAMLIT_SERVER_PORT=8501
set STREAMLIT_SERVER_ENABLE_CORS=false
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_CLIENT_CACHING=true

echo Starting with speed optimizations...
streamlit run integrated_dashboard.py --server.port 8501 --server.enableCORS false --browser.gatherUsageStats false

echo Demo session ended.
pause
