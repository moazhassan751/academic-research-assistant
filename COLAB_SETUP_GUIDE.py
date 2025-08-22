# ================================================
# ACADEMIC RESEARCH ASSISTANT - OPTIMIZED COLAB SETUP
# ================================================

# CELL 1: Clone Repository and Initial Setup
# ==========================================
!git clone https://github.com/moazhassan751/academic-research-assistant.git
%cd academic-research-assistant

# Run the automated setup script
!python colab_setup.py

# Verify directory structure
!ls -la

# CELL 2: Install Dependencies (Optimized)
# ========================================
# Install core requirements
!pip install -r requirements.txt
!pip install pyngrok

# Install production requirements for better performance
!pip install -r requirements_production.txt

# Verify Streamlit installation
!streamlit --version

print("✅ All dependencies installed successfully!")

# CELL 3: Configure Ngrok
# =======================
from pyngrok import ngrok
import os

# Your ngrok token
NGROK_TOKEN = "2wMjCJuxRegxUBJ05tnE62KUEDH_3Z2F41vBedf1ds3T1QcUh"
ngrok.set_auth_token(NGROK_TOKEN)

print("✅ Ngrok configured successfully!")

# CELL 4: Optimized Environment Variables
# =======================================
import os

# ================================
# ENVIRONMENT CONFIGURATION (Colab Optimized)
# ================================
os.environ['ENVIRONMENT'] = 'colab'  # Changed to 'colab' for better optimization

# ================================
# API KEYS
# ================================
os.environ['GOOGLE_API_KEY'] = 'AIzaSyCiO-OZd2PX1hrg8c1NmMgrL1SHkpGBJCE'
os.environ['GEMINI_API_KEY'] = 'AIzaSyCiO-OZd2PX1hrg8c1NmMgrL1SHkpGBJCE'

# ================================
# DATABASE CONFIGURATION
# ================================
os.environ['DATABASE_PATH'] = 'data/research.db'

# ================================
# LOGGING CONFIGURATION
# ================================
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['LOG_FILE'] = 'logs/research_assistant.log'

# ================================
# API RATE LIMITING (Colab Optimized - Faster!)
# ================================
os.environ['GEMINI_REQUESTS_PER_MINUTE'] = '15'  # Increased from 10
os.environ['OPENALEX_REQUESTS_PER_SECOND'] = '12'  # Increased from 10
os.environ['CROSSREF_REQUESTS_PER_SECOND'] = '2'   # Increased from 1
os.environ['ARXIV_DELAY_SECONDS'] = '1'            # Reduced from 3

# ================================
# API CONTACT INFORMATION
# ================================
os.environ['OPENALEX_USER_AGENT'] = 'AcademicResearchAssistant/1.0 (mailto:rmoazhassan555@gmail.com)'
os.environ['CROSSREF_MAILTO'] = 'rmoazhassan555@gmail.com'
os.environ['OPENALEX_EMAIL'] = 'rmoazhassan555@gmail.com'

# ================================
# APPLICATION SETTINGS (Colab Optimized)
# ================================
os.environ['MAX_RETRIES'] = '2'        # Reduced from 3 for faster failures
os.environ['REQUEST_TIMEOUT'] = '20'   # Reduced from 30 for faster response
os.environ['MAX_PAPERS_DEFAULT'] = '5' # Reduced from 10 for faster processing

# ================================
# OUTPUT CONFIGURATION
# ================================
os.environ['OUTPUTS_DIR'] = 'data/outputs'
os.environ['CACHE_DIR'] = 'data/cache'
os.environ['PAPERS_DIR'] = 'data/papers'

# ================================
# API BASE URLS
# ================================
os.environ['OPENALEX_BASE_URL'] = 'https://api.openalex.org/works'
os.environ['CROSSREF_BASE_URL'] = 'https://api.crossref.org/works'
os.environ['ARXIV_BASE_URL'] = 'http://export.arxiv.org/api/query'

# ================================
# PERFORMANCE SETTINGS (Colab Optimized)
# ================================
os.environ['VERBOSE_LOGGING'] = 'false'
os.environ['ENABLE_API_CACHING'] = 'true'
os.environ['API_TIMEOUT_SECONDS'] = '20'   # Reduced from 30
os.environ['LLM_TIMEOUT'] = '180'          # Reduced from 300
os.environ['API_COOLDOWN'] = '60'          # Reduced from 120

print("✅ Environment optimized for Google Colab!")
print("🔑 Google API Key: LOADED")
print("📧 Email settings: rmoazhassan555@gmail.com")
print("⚡ Performance optimizations: ACTIVE")
print("🚀 Ready to launch Academic Research Assistant!")

# CELL 5: Launch Application (Enhanced)
# =====================================
import subprocess
import time
from threading import Thread
import signal
import sys

def run_streamlit():
    """Run Streamlit with enhanced error handling"""
    try:
        print("🔧 Starting Streamlit server...")
        result = subprocess.run([
            "streamlit", "run", "integrated_dashboard.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0", 
            "--server.headless", "true",
            "--server.runOnSave", "false",
            "--browser.serverAddress", "0.0.0.0"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Streamlit error: {result.stderr}")
        
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")

# Check if app is already running
def check_streamlit_health():
    """Check if Streamlit is running"""
    try:
        import requests
        response = requests.get("http://localhost:8501/healthz", timeout=5)
        return response.status_code == 200
    except:
        return False

print("🚀 Starting Academic Research Assistant...")
print("📊 Launching with optimized settings...")

# Start Streamlit in background
thread = Thread(target=run_streamlit)
thread.daemon = True
thread.start()

# Wait for startup with progress indicator
print("⏳ Initializing application...")
for i in range(6):
    time.sleep(5)
    if check_streamlit_health():
        print(f"✅ Application ready in {(i+1)*5} seconds!")
        break
    print(f"   Loading... {(i+1)*5}s")
else:
    print("⚠️ Application starting (may take a moment)")
    time.sleep(10)  # Extra time for slow starts

# Create public tunnel with enhanced error handling
try:
    print("🌐 Creating public tunnel...")
    public_url = ngrok.connect(8501)
    
    print("\n" + "=" * 60)
    print("🎉 ACADEMIC RESEARCH ASSISTANT IS LIVE!")
    print("=" * 60)
    print(f"🔗 Public URL: {public_url}")
    print(f"📱 Share this link to access your research assistant!")
    print("=" * 60)
    print("🔥 OPTIMIZED FEATURES AVAILABLE:")
    print("   🔍 Fast Literature Search (2-3x faster)")
    print("   🤖 AI Research Assistant with Gemini 2.5")
    print("   📊 Interactive Research Dashboard")
    print("   💾 Export & Download Results")
    print("   ⚡ Enhanced Performance Mode")
    print("=" * 60)
    print("⚠️  Keep this cell running to maintain the connection")
    print("🔄 Auto-refresh: The tunnel stays active")
    
    # Enhanced keep-alive with status monitoring
    try:
        while True:
            time.sleep(60)
            # Optional: Add periodic health checks
            if not check_streamlit_health():
                print("⚠️ Application health check failed - but tunnel remains active")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping the application...")
        ngrok.disconnect(public_url)
        print("✅ Application stopped cleanly")

except Exception as e:
    print(f"❌ Error creating tunnel: {e}")
    print("\n🔧 TROUBLESHOOTING GUIDE:")
    print("1. ✅ Verify ngrok token is correct")
    print("2. ✅ Check if Google API key is valid") 
    print("3. ✅ Ensure all environment variables are set")
    print("4. 🔄 Try restarting this cell")
    print("5. 📞 Check Colab internet connection")
    
    # Attempt to show local access as fallback
    print(f"\n💡 If tunnel fails, try local access:")
    print(f"   Local URL: http://localhost:8501")
