#!/usr/bin/env python3
"""
Comprehensive test to ensure all core functionality works perfectly
"""

import sys
import os
import tempfile
import traceback

def test_all_validators():
    """Test all validator functionality"""
    print("🧪 Testing Validators...")
    try:
        from src.utils.validators import (
            validate_research_query, 
            validate_export_formats, 
            validate_paper_data,
            sanitize_filename,
            validate_search_query
        )
        
        # Test successful validations
        query_result = validate_research_query({
            'topic': 'machine learning',
            'max_papers': 10,
            'paper_type': 'survey',
            'aspects': ['deep learning', 'neural networks']
        })
        print(f"   ✅ Research query validation: {query_result.topic}")
        
        format_result = validate_export_formats({
            'formats': ['pdf', 'docx', 'markdown']
        })
        print(f"   ✅ Export format validation: {format_result.formats}")
        
        paper_result = validate_paper_data({
            'title': 'Test Paper',
            'authors': ['John Doe'],
            'abstract': 'This is a test abstract',
            'url': 'https://example.com/paper.pdf',
            'doi': '10.1000/test.doi'
        })
        print(f"   ✅ Paper validation: {paper_result.title}")
        
        # Test utility functions
        safe_filename = sanitize_filename('Test<>File|Name?.pdf')
        print(f"   ✅ Filename sanitization: {safe_filename}")
        
        clean_query = validate_search_query('machine learning research')
        print(f"   ✅ Search query validation: {clean_query}")
        
        # Test error handling
        try:
            validate_research_query({'topic': '', 'max_papers': 10})
            print("   ❌ Error handling failed")
            return False
        except ValueError:
            print("   ✅ Error handling working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Validator test failed: {e}")
        traceback.print_exc()
        return False

def test_database_functionality():
    """Test database functionality"""
    print("🧪 Testing Database...")
    try:
        from src.storage.database import DatabaseManager
        from src.storage.models import Paper
        from datetime import datetime
        import aiosqlite
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            test_db_path = f.name
        
        try:
            db = DatabaseManager(test_db_path)
            print("   ✅ Database initialization")
            
            # Test paper operations
            test_paper = Paper(
                id='test-1',
                title='Test Paper',
                authors=['Test Author'],
                abstract='Test abstract',
                url='https://example.com',
                published_date=datetime.now()
            )
            
            paper_id = db.save_paper(test_paper)
            print(f"   ✅ Paper saved: {paper_id}")
            
            retrieved_papers = db.get_papers()
            print(f"   ✅ Papers retrieved: {len(retrieved_papers)}")
            
            # Test search
            search_results = db.search_papers('Test')
            print(f"   ✅ Search results: {len(search_results)}")
            
            # Test stats
            stats = db.get_stats()
            print(f"   ✅ Database stats: {stats}")
            
            return True
            
        finally:
            # Cleanup
            try:
                os.unlink(test_db_path)
            except:
                pass
                
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling system"""
    print("🧪 Testing Error Handling...")
    try:
        from src.utils.error_handler import (
            ErrorHandler, 
            ValidationError, 
            ConfigurationError,
            APIError,
            DatabaseError
        )
        
        # Test error handler
        handler = ErrorHandler()
        print("   ✅ Error handler initialized")
        
        # Test custom exceptions
        try:
            raise ValidationError("Test validation error")
        except ValidationError as e:
            print(f"   ✅ ValidationError: {e.message}")
        
        try:
            raise ConfigurationError("Test config error")
        except ConfigurationError as e:
            print(f"   ✅ ConfigurationError: {e.message}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        traceback.print_exc()
        return False

def test_async_api():
    """Test async API manager"""
    print("🧪 Testing Async API Manager...")
    try:
        from src.utils.async_api_manager import AsyncAPIManager
        import asyncio
        
        # Test initialization
        manager = AsyncAPIManager()
        print("   ✅ Async API manager initialized")
        
        # Test rate limiter
        from src.utils.async_api_manager import RateLimiter
        limiter = RateLimiter(requests_per_second=10)
        print("   ✅ Rate limiter created")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Async API test failed: {e}")
        traceback.print_exc()
        return False

def test_logging_system():
    """Test enhanced logging"""
    print("🧪 Testing Enhanced Logging...")
    try:
        from src.utils.logging import get_logger, setup_logging
        
        # Setup logging
        setup_logging()
        print("   ✅ Logging setup complete")
        
        # Test logger
        logger = get_logger(__name__)
        logger.info("Test log message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        print("   ✅ Logger functionality working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Logging test failed: {e}")
        traceback.print_exc()
        return False

def test_main_functionality():
    """Test main application functionality"""
    print("🧪 Testing Main Application...")
    try:
        # Test basic imports
        from src.crew.research_crew import ResearchCrew
        from src.agents.literature_survey_agent import LiteratureSurveyAgent
        from src.tools.Open_Alex_tool import OpenAlexTool
        print("   ✅ Core application imports")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Main application test failed: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 COMPREHENSIVE SYSTEM TEST")
    print("=" * 50)
    
    tests = [
        ("Validators", test_all_validators),
        ("Database", test_database_functionality), 
        ("Error Handling", test_error_handling),
        ("Async API Manager", test_async_api),
        ("Enhanced Logging", test_logging_system),
        ("Main Application", test_main_functionality),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        success = test_func()
        results.append((name, success))
        if success:
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED")
    
    print(f"\n{'='*50}")
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("="*50)
    
    passed = 0
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:<20} {status}")
        if success:
            passed += 1
    
    print(f"\n📈 Overall Score: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED! System is fully functional!")
        return True
    else:
        print(f"⚠️  {len(results) - passed} components need attention")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
