Write-Host "Starting OPTIMIZED Academic Research Assistant Demo..." -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Blue

# Set demo environment variables
$env:STREAMLIT_SERVER_PORT = "8501"
$env:STREAMLIT_SERVER_ENABLE_CORS = "false"
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
$env:STREAMLIT_CLIENT_CACHING = "true"

Write-Host "Starting with speed optimizations..." -ForegroundColor Yellow
streamlit run integrated_dashboard.py --server.port 8501 --server.enableCORS false --browser.gatherUsageStats false

Write-Host "Demo session ended." -ForegroundColor Green
Read-Host "Press Enter to exit"
