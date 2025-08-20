#!/usr/bin/env python3
"""
Test script to check the functionality of integrated_dashboard.py
"""

import sys
import os
from pathlib import Path
import traceback

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all required imports work"""
    print("🔍 Testing imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        print("✅ Data visualization libraries imported successfully")
    except ImportError as e:
        print(f"❌ Data visualization libraries import failed: {e}")
        return False
    
    # Test research functionality imports
    try:
        from src.crew.research_crew import ResearchCrew
        from src.storage.database import db
        from src.utils.config import config
        from src.utils.export_manager import export_manager
        from src.agents.qa_agent import QuestionAnsweringAgent
        from src.utils.logging import setup_logging, logger
        print("✅ Research functionality imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Research functionality import failed: {e}")
        print("   This is expected if dependencies are not installed")
        return False

def test_database_connection():
    """Test database connection and basic operations"""
    print("\n📊 Testing database connection...")
    
    try:
        from src.storage.database import db
        
        # Test database stats
        stats = db.get_stats()
        print(f"✅ Database stats: {stats}")
        
        # Test recent papers
        recent_papers = db.get_recent_papers(5)
        print(f"✅ Recent papers count: {len(recent_papers)}")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from src.utils.config import config
        
        env = config.environment
        llm_config = config.llm_config
        
        print(f"✅ Environment: {env}")
        print(f"✅ LLM Config: {llm_config}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_research_crew_init():
    """Test ResearchCrew initialization"""
    print("\n🔬 Testing ResearchCrew initialization...")
    
    try:
        from src.crew.research_crew import ResearchCrew
        
        crew = ResearchCrew()
        print("✅ ResearchCrew initialized successfully")
        
        # Test available export formats
        try:
            formats = crew.get_available_export_formats()
            print(f"✅ Available export formats: {formats}")
        except Exception as e:
            print(f"⚠️ Export formats test failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ ResearchCrew initialization failed: {e}")
        traceback.print_exc()
        return False

def test_qa_agent_init():
    """Test QA Agent initialization"""
    print("\n❓ Testing QA Agent initialization...")
    
    try:
        from src.agents.qa_agent import QuestionAnsweringAgent
        
        qa_agent = QuestionAnsweringAgent()
        print("✅ QA Agent initialized successfully")
        
        return True
    except Exception as e:
        print(f"❌ QA Agent initialization failed: {e}")
        traceback.print_exc()
        return False

def test_export_manager():
    """Test export manager functionality"""
    print("\n📤 Testing export manager...")
    
    try:
        from src.utils.export_manager import export_manager
        
        print("✅ Export manager imported successfully")
        
        # You could test specific export methods here
        return True
    except Exception as e:
        print(f"❌ Export manager test failed: {e}")
        return False

def test_logging():
    """Test logging setup"""
    print("\n📝 Testing logging...")
    
    try:
        from src.utils.logging import setup_logging, logger
        
        setup_logging('INFO')
        logger.info("Test log message")
        print("✅ Logging setup successful")
        
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def run_all_tests():
    """Run all functionality tests"""
    print("🧪 Running integrated_dashboard.py functionality tests...")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Database Connection", test_database_connection),
        ("Configuration", test_configuration),
        ("Research Crew", test_research_crew_init),
        ("QA Agent", test_qa_agent_init),
        ("Export Manager", test_export_manager),
        ("Logging", test_logging)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20}: {status}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The integrated dashboard should work correctly.")
    elif passed > total // 2:
        print("⚠️ Most tests passed. Some features may not work completely.")
    else:
        print("❌ Many tests failed. Check your installation and dependencies.")
    
    return results

if __name__ == "__main__":
    run_all_tests()
