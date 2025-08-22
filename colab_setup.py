#!/usr/bin/env python3
"""
Colab Setup Script for Academic Research Assistant
==================================================
This script prepares the environment for running on Google Colab
"""

import os
import sys
from pathlib import Path

def setup_colab_environment():
    """Setup the environment for Google Colab"""
    print("🚀 Setting up Academic Research Assistant for Google Colab...")
    print("=" * 60)
    
    # Create required directories
    required_dirs = [
        'logs',
        'data',
        'data/cache',
        'data/outputs', 
        'data/papers',
        'config',
        'config_backups'
    ]
    
    print("📁 Creating required directories...")
    for dir_path in required_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"   ✅ {dir_path}")
    
    # Create empty log files to prevent errors
    log_files = [
        'logs/production_errors.log',
        'logs/research_assistant.log',
        'logs/errors.log'
    ]
    
    print("\n📝 Creating log files...")
    for log_file in log_files:
        Path(log_file).touch()
        print(f"   ✅ {log_file}")
    
    # Create default database if it doesn't exist
    db_path = 'data/research.db'
    if not os.path.exists(db_path):
        print(f"\n🗄️ Creating database: {db_path}")
        try:
            from src.storage.database import DatabaseManager
            db = DatabaseManager()
            print("   ✅ Database initialized")
        except Exception as e:
            print(f"   ⚠️ Database initialization deferred: {e}")
    
    # Set Colab-specific environment variables
    print("\n⚙️ Setting Colab environment variables...")
    colab_env_vars = {
        'ENVIRONMENT': 'colab',
        'STREAMLIT_SERVER_PORT': '8501',
        'STREAMLIT_SERVER_ADDRESS': '0.0.0.0',
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'PYTHONPATH': '/content/academic-research-assistant'
    }
    
    for key, value in colab_env_vars.items():
        os.environ[key] = value
        print(f"   ✅ {key}={value}")
    
    print("\n🎉 Colab environment setup complete!")
    print("=" * 60)
    print("✅ All directories created")
    print("✅ Log files initialized") 
    print("✅ Environment variables set")
    print("✅ Ready to run Academic Research Assistant!")
    
    return True

if __name__ == "__main__":
    setup_colab_environment()
