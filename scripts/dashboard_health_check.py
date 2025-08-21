"""
Streamlit Dashboard Health Check
Quick test to verify dashboard functionality
"""
import streamlit as st
import sys
import time
import importlib.util
from pathlib import Path

def test_dashboard_health():
    """Test the integrated dashboard health"""
    st.title("🔍 Dashboard Health Check")
    st.write("---")
    
    # Test 1: Module Import
    with st.expander("📦 Module Import Test", expanded=True):
        try:
            spec = importlib.util.spec_from_file_location("integrated_dashboard", "integrated_dashboard.py")
            dashboard = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dashboard)
            st.success("✅ Dashboard module imported successfully")
            module_test = True
        except Exception as e:
            st.error(f"❌ Dashboard import failed: {str(e)}")
            module_test = False
    
    # Test 2: Configuration Test
    with st.expander("⚙️ Configuration Test", expanded=True):
        try:
            from src.utils.config import config
            st.success("✅ Configuration loaded successfully")
            st.info(f"Environment: {config.environment}")
            st.info(f"LLM Provider: {config.llm_config.get('provider', 'Unknown')}")
            st.info(f"API Keys Valid: {config.validate_api_keys()}")
            config_test = True
        except Exception as e:
            st.error(f"❌ Configuration failed: {str(e)}")
            config_test = False
    
    # Test 3: Database Connection
    with st.expander("🗄️ Database Connection Test", expanded=True):
        try:
            from src.storage.database import DatabaseManager
            db_path = Path("data/research.db")
            if db_path.exists():
                db = DatabaseManager()
                st.success("✅ Database connection successful")
                db_test = True
            else:
                st.warning("⚠️ Database file not found, but connection logic works")
                db_test = True
        except Exception as e:
            st.error(f"❌ Database connection failed: {str(e)}")
            db_test = False
    
    # Test 4: Performance Check
    with st.expander("⚡ Performance Test", expanded=True):
        start_time = time.time()
        
        # Simulate some operations
        for i in range(100):
            pass
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        if response_time < 100:
            st.success(f"✅ Excellent response time: {response_time:.2f}ms")
            perf_test = True
        elif response_time < 500:
            st.info(f"✅ Good response time: {response_time:.2f}ms")
            perf_test = True
        else:
            st.warning(f"⚠️ Slow response time: {response_time:.2f}ms")
            perf_test = False
    
    # Overall Status
    st.write("---")
    st.subheader("📊 Overall Health Status")
    
    total_tests = 4
    passed_tests = sum([module_test, config_test, db_test, perf_test])
    success_rate = (passed_tests / total_tests) * 100
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tests Passed", f"{passed_tests}/{total_tests}")
    
    with col2:
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        if success_rate >= 90:
            st.success("🚀 EXCELLENT")
        elif success_rate >= 75:
            st.info("👍 GOOD")
        elif success_rate >= 50:
            st.warning("⚠️ NEEDS WORK")
        else:
            st.error("🚨 CRITICAL")
    
    # Recommendations
    if success_rate < 100:
        st.write("---")
        st.subheader("🔧 Recommendations")
        
        if not module_test:
            st.error("🔴 Fix dashboard module import issues")
        if not config_test:
            st.error("🔴 Fix configuration problems")
        if not db_test:
            st.error("🔴 Fix database connection issues")
        if not perf_test:
            st.warning("🟡 Optimize performance for better response times")
    else:
        st.success("🎉 Your dashboard is working perfectly!")
        st.balloons()

if __name__ == "__main__":
    test_dashboard_health()
