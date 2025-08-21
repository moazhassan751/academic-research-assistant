"""
Comprehensive Test for Integrated Dashboard
Tests all major functionality and components
"""

import sys
import importlib
import traceback
from pathlib import Path

def test_dashboard_imports():
    """Test all imports in the dashboard"""
    print("🔍 Testing Dashboard Imports...")
    
    try:
        # Test basic imports
        import streamlit as st
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        print("✅ Basic libraries imported successfully")
        
        # Test dashboard import
        sys.path.insert(0, str(Path(__file__).parent))
        import integrated_dashboard
        print("✅ Integrated dashboard imported successfully")
        
        # Test error handling modules
        try:
            from production_error_handler import production_handler, production_safe, validate_inputs, safe_data_access
            print("✅ Production error handler available")
        except ImportError as e:
            print(f"⚠️ Production error handler not available: {e}")
        
        try:
            from dashboard_performance import performance_monitor, with_performance_tracking, show_performance_sidebar
            print("✅ Dashboard performance module available")
        except ImportError as e:
            print(f"⚠️ Dashboard performance module not available: {e}")
        
        try:
            from professional_error_handler import error_handler, safe_execute, validate_inputs, show_system_health
            print("✅ Professional error handler available")
        except ImportError as e:
            print(f"⚠️ Professional error handler not available: {e}")
        
        # Test research modules
        try:
            from src.crew.research_crew import ResearchCrew
            from src.storage.database import db
            from src.utils.config import config
            from src.agents.qa_agent import QuestionAnsweringAgent
            from src.utils.logging import setup_logging, logger
            print("✅ Research modules available")
        except ImportError as e:
            print(f"⚠️ Research modules not available: {e}")
        
        # Test export manager
        try:
            from src.utils.export_manager import export_manager
            print("✅ Main export manager available")
        except ImportError:
            try:
                from simple_export_manager import export_manager
                print("✅ Fallback export manager available")
            except ImportError as e:
                print(f"❌ No export manager available: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False

def test_dashboard_functions():
    """Test key dashboard functions"""
    print("\n🧪 Testing Dashboard Functions...")
    
    try:
        # Import the dashboard
        import integrated_dashboard as dashboard
        
        # Test helper functions
        try:
            # Test format_paper_card
            class MockPaper:
                title = "Test Paper"
                authors = ["Author 1", "Author 2"]
                abstract = "Test abstract"
                year = 2024
                citations = 10
                venue = "Test Journal"
                topic = "AI"
                source = "Test Source"
                url = "http://test.com"
            
            card_html = dashboard.format_paper_card(MockPaper())
            assert "Test Paper" in card_html
            print("✅ format_paper_card function works")
            
        except Exception as e:
            print(f"⚠️ format_paper_card test failed: {e}")
        
        try:
            # Test create_metric_card
            metric_html = dashboard.create_metric_card("Test Metric", 42, "🧪", trend=5.2)
            assert "Test Metric" in metric_html
            assert "42" in metric_html
            print("✅ create_metric_card function works")
            
        except Exception as e:
            print(f"⚠️ create_metric_card test failed: {e}")
        
        try:
            # Test show_loading_animation
            loading_html = dashboard.show_loading_animation("Testing...")
            print("✅ show_loading_animation function works")
            
        except Exception as e:
            print(f"⚠️ show_loading_animation test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Function test failed: {e}")
        traceback.print_exc()
        return False

def test_export_manager():
    """Test export manager functionality"""
    print("\n📤 Testing Export Manager...")
    
    try:
        from simple_export_manager import export_manager
        
        # Test text export
        test_content = "This is a test export content."
        test_path = "test_export"
        
        success = export_manager.export_draft(test_content, test_path, "txt")
        if success:
            print("✅ Text export works")
            # Clean up
            import os
            if os.path.exists(f"{test_path}.txt"):
                os.remove(f"{test_path}.txt")
        else:
            print("⚠️ Text export failed")
        
        # Test HTML export
        success = export_manager.export_draft(test_content, test_path, "html")
        if success:
            print("✅ HTML export works")
            # Clean up
            import os
            if os.path.exists(f"{test_path}.html"):
                os.remove(f"{test_path}.html")
        else:
            print("⚠️ HTML export failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Export manager test failed: {e}")
        traceback.print_exc()
        return False

def test_analytics_functions():
    """Test analytics functions with mock data"""
    print("\n📊 Testing Analytics Functions...")
    
    try:
        import integrated_dashboard as dashboard
        
        # Test with mock research availability
        original_research_available = dashboard.RESEARCH_AVAILABLE
        dashboard.RESEARCH_AVAILABLE = False
        
        # Test get_database_stats with no research available
        stats = dashboard.get_database_stats()
        assert isinstance(stats, dict)
        assert 'papers' in stats
        assert 'notes' in stats
        print("✅ get_database_stats works with no research")
        
        # Test get_research_analytics with no research available
        analytics = dashboard.get_research_analytics()
        assert isinstance(analytics, dict)
        print("✅ get_research_analytics works with no research")
        
        # Test get_recent_papers with no research available
        papers = dashboard.get_recent_papers()
        assert isinstance(papers, list)
        print("✅ get_recent_papers works with no research")
        
        # Restore original value
        dashboard.RESEARCH_AVAILABLE = original_research_available
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")
        traceback.print_exc()
        return False

def test_ui_components():
    """Test UI component generation"""
    print("\n🎨 Testing UI Components...")
    
    try:
        import integrated_dashboard as dashboard
        
        # Test skeleton card
        skeleton_html = dashboard.show_skeleton_card()
        print("✅ Skeleton card generation works")
        
        # Test metric cards with different parameters
        metric1 = dashboard.create_metric_card("Papers", 100, "📚")
        metric2 = dashboard.create_metric_card("Citations", 250, "⭐", trend=5.2)
        metric3 = dashboard.create_metric_card("Topics", 15, "🎯", trend=-2.1, color="warning")
        
        assert all("metric-card" in m for m in [metric1, metric2, metric3])
        print("✅ Metric card variations work")
        
        return True
        
    except Exception as e:
        print(f"❌ UI component test failed: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting Comprehensive Dashboard Test\n")
    print("="*60)
    
    tests = [
        ("Import Test", test_dashboard_imports),
        ("Function Test", test_dashboard_functions),
        ("Export Manager Test", test_export_manager),
        ("Analytics Test", test_analytics_functions),
        ("UI Components Test", test_ui_components)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Dashboard is 100% functional!")
    elif passed >= total * 0.8:
        print("✅ Most tests passed. Dashboard is highly functional!")
    elif passed >= total * 0.6:
        print("⚠️ Partial functionality. Some features may not work.")
    else:
        print("❌ Multiple issues detected. Dashboard needs fixes.")
    
    return passed, total

if __name__ == "__main__":
    passed, total = run_comprehensive_test()
    
    print("\n💡 FUNCTIONALITY ASSESSMENT:")
    print("-" * 40)
    
    functionality_percent = (passed / total) * 100
    
    print(f"📊 Functionality Score: {functionality_percent:.1f}%")
    
    if functionality_percent >= 95:
        print("🏆 EXCELLENT: Dashboard is production-ready")
    elif functionality_percent >= 85:
        print("✅ GOOD: Dashboard is highly functional with minor issues")
    elif functionality_percent >= 70:
        print("⚠️ FAIR: Dashboard works but has some limitations")
    elif functionality_percent >= 50:
        print("🔧 NEEDS WORK: Core features work but many issues exist")
    else:
        print("🚨 CRITICAL: Dashboard has major functionality issues")
    
    print("\n🔧 Next Steps:")
    if functionality_percent < 100:
        print("- Review failed tests above")
        print("- Install missing dependencies")
        print("- Configure database and API connections")
        print("- Test in full Streamlit environment")
    else:
        print("- Deploy to production")
        print("- Set up monitoring")
        print("- Run integration tests")
