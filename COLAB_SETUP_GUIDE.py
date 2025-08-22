# ACADEMIC RESEARCH ASSISTANT - GOOGLE COLAB SETUP
# ================================================
# Copy and paste this code into Google Colab cells

# CELL 1: Clone Repository and Basic Setup
# ==========================================
!git clone https://github.com/moazhassan751/academic-research-assistant.git
%cd academic-research-assistant

# Run Colab setup script
!python colab_setup.py

# CELL 2: Install Requirements  
# ============================
!pip install -r requirements.txt
!pip install pyngrok streamlit

# Verify installation
!streamlit --version

# CELL 3: Configure Environment Variables
# ======================================
import os

# ================================
# ENVIRONMENT CONFIGURATION
# ================================
os.environ['ENVIRONMENT'] = 'colab'

# ================================
# API KEYS - REPLACE WITH YOUR ACTUAL KEYS
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
# API RATE LIMITING (Optimized for Colab)
# ================================
os.environ['GEMINI_REQUESTS_PER_MINUTE'] = '15'
os.environ['OPENALEX_REQUESTS_PER_SECOND'] = '12'
os.environ['CROSSREF_REQUESTS_PER_SECOND'] = '2'
os.environ['ARXIV_DELAY_SECONDS'] = '1'

# ================================
# API CONTACT INFORMATION
# ================================
os.environ['OPENALEX_USER_AGENT'] = 'AcademicResearchAssistant/1.0 (mailto:rmoazhassan555@gmail.com)'
os.environ['CROSSREF_MAILTO'] = 'rmoazhassan555@gmail.com'
os.environ['OPENALEX_EMAIL'] = 'rmoazhassan555@gmail.com'

# ================================
# APPLICATION SETTINGS (Colab Optimized)
# ================================
os.environ['MAX_RETRIES'] = '2'
os.environ['REQUEST_TIMEOUT'] = '20'
os.environ['MAX_PAPERS_DEFAULT'] = '5'
os.environ['API_TIMEOUT_SECONDS'] = '20'
os.environ['LLM_TIMEOUT'] = '180'
os.environ['API_COOLDOWN'] = '60'

print("✅ Environment configured for Google Colab!")

# CELL 4: Setup Ngrok Tunnel
# ==========================
from pyngrok import ngrok

# Replace with your actual ngrok token
NGROK_TOKEN = "2wMjCJuxRegxUBJ05tnE62KUEDH_3Z2F41vBedf1ds3T1QcUh"
ngrok.set_auth_token(NGROK_TOKEN)

print("✅ Ngrok configured successfully!")

# CELL 5: Launch Application
# ==========================
import subprocess
import time
from threading import Thread

def run_streamlit():
    """Run Streamlit in background"""
    try:
        subprocess.run([
            "streamlit", "run", "integrated_dashboard.py",
            "--server.port", "8501", 
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ])
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")

# Start Streamlit
print("🚀 Starting Academic Research Assistant...")
thread = Thread(target=run_streamlit)
thread.daemon = True
thread.start()

# Wait for startup
print("⏳ Waiting for application to start...")
time.sleep(25)

# Create public tunnel
try:
    public_url = ngrok.connect(8501)
    print("=" * 60)
    print("🎉 SUCCESS! Academic Research Assistant is LIVE!")
    print("=" * 60)
    print(f"🔗 Public URL: {public_url}")
    print(f"📱 Share this link to access your research assistant!")
    print("=" * 60)
    print("📚 Features available:")
    print("   • Literature Search & Analysis")
    print("   • AI-Powered Research Assistance") 
    print("   • Export & Download Results")
    print("   • Interactive Research Dashboard")
    print("=" * 60)
    print("⚠️  Keep this cell running to maintain the connection")
    
    # Keep alive
    while True:
        time.sleep(60)
        
except KeyboardInterrupt:
    print("🛑 Stopping application...")
    ngrok.disconnect(public_url)
except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 Troubleshooting:")
    print("   1. Verify your ngrok token is correct")
    print("   2. Check if all environment variables are set")
    print("   3. Ensure Google API key is valid")
