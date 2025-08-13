#!/usr/bin/env python3
"""
Test script to verify all the fixes work correctly
"""

import sys
import traceback

def test_validators():
    """Test validators import and functionality"""
    try:
        from src.utils.validators import validate_research_query, validate_export_formats, validate_paper_data
        
        # Test successful validation
        result = validate_research_query({'topic': 'machine learning', 'max_papers': 10})
        print(f"✅ Validators working - topic: {result.topic}")
        
        # Test validation error handling
        try:
            validate_research_query({'topic': '', 'max_papers': 10})
        except ValueError as e:
            print(f"✅ Validation error handling working: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Validators test failed: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Test database import"""
    try:
        import aiosqlite
        from src.storage.database import DatabaseManager
        print("✅ Database imports working")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False

def test_error_handler():
    """Test error handler"""
    try:
        from src.utils.error_handler import ValidationError, ConfigurationError
        print("✅ Error handler imports working")
        return True
    except Exception as e:
        print(f"❌ Error handler test failed: {e}")
        traceback.print_exc()
        return False

def test_async_api():
    """Test async API manager"""
    try:
        from src.utils.async_api_manager import AsyncAPIManager
        print("✅ Async API manager imports working")
        return True
    except Exception as e:
        print(f"❌ Async API manager test failed: {e}")
        traceback.print_exc()
        return False

def test_logging():
    """Test enhanced logging"""
    try:
        from src.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Test log message")
        print("✅ Enhanced logging working")
        return True
    except Exception as e:
        print(f"❌ Enhanced logging test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Running component tests...\n")
    
    tests = [
        ("Validators", test_validators),
        ("Database", test_database),
        ("Error Handler", test_error_handler),
        ("Async API Manager", test_async_api),
        ("Enhanced Logging", test_logging),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        success = test_func()
        results.append((name, success))
    
    print(f"\n{'='*50}")
    print("📊 Test Results Summary:")
    print("="*50)
    
    passed = 0
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:<20} {status}")
        if success:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{len(results)} components working")
    
    if passed == len(results):
        print("🎉 All core components are working!")
        sys.exit(0)
    else:
        print("⚠️  Some components need attention")
        sys.exit(1)
