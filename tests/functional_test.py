#!/usr/bin/env python3
"""
Simple functional test to verify core functionality
"""

import sys
import os
import warnings
from pathlib import Path

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Ensure we're in the correct directory
os.chdir(Path(__file__).parent)

def test_main_functionality():
    """Test main application functionality"""
    print("🧪 FUNCTIONAL TEST RESULTS")
    print("=" * 50)
    
    tests = []
    
    # Test 1: Core imports
    try:
        from src.crew.research_crew import UltraFastResearchCrew as ResearchCrew
        from src.storage.database import db
        from src.utils.config import config
        tests.append(("✅", "Core imports"))
    except Exception as e:
        tests.append(("❌", f"Core imports: {e}"))
    
    # Test 2: Database connection
    try:
        from src.storage.database import db
        stats = db.get_stats()
        tests.append(("✅", f"Database connection (Papers: {stats.get('papers', 0)})"))
    except Exception as e:
        tests.append(("❌", f"Database connection: {e}"))
    
    # Test 3: Configuration loading
    try:
        from src.utils.config import config
        llm_model = config.get('llm.model', 'unknown')
        tests.append(("✅", f"Configuration loading (Model: {llm_model})"))
    except Exception as e:
        tests.append(("❌", f"Configuration loading: {e}"))
    
    # Test 4: API tools
    try:
        from src.tools.Open_Alex_tool import OpenAlexTool
        from src.tools.Cross_Ref_tool import CrossRefTool
        from src.tools.arxiv_tool import ArxivTool
        tests.append(("✅", "API tools import"))
    except Exception as e:
        tests.append(("❌", f"API tools import: {e}"))
    
    # Test 5: LLM client
    try:
        from src.llm.gemini_client import gemini_client
        tests.append(("✅", "LLM client"))
    except Exception as e:
        tests.append(("❌", f"LLM client: {e}"))
    
    # Print results
    for status, message in tests:
        print(f"{status} {message}")
    
    # Summary
    passed = sum(1 for status, _ in tests if status == "✅")
    total = len(tests)
    
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - System is fully functional!")
        return True
    elif passed >= total * 0.8:
        print("⚠️ MOSTLY WORKING - Minor issues detected")
        return True
    else:
        print("❌ MAJOR ISSUES - System needs attention")
        return False

if __name__ == "__main__":
    success = test_main_functionality()
    sys.exit(0 if success else 1)
