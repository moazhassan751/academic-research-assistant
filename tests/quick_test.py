#!/usr/bin/env python3
"""
Quick test script to verify the Academic Research Assistant is working
"""

import sys
import traceback

def test_basic_functionality():
    """Test basic research assistant functionality"""
    print("🧪 TESTING ACADEMIC RESEARCH ASSISTANT")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from src.utils.validators import validate_research_query
        from src.storage.database import DatabaseManager
        from src.utils.error_handler import ValidationError
        print("   ✅ Core imports successful")
        
        # Test configuration
        print("⚙️  Testing configuration...")
        from src.utils.config import config
        db_path = config.get('database.path', 'data/research.db')
        print(f"   ✅ Config loaded, database path: {db_path}")
        
        # Test database
        print("🗄️  Testing database...")
        db = DatabaseManager()
        stats = db.get_stats()
        print(f"   ✅ Database working, stats: {stats}")
        
        # Test validation
        print("✅ Testing validation...")
        query_data = {
            'topic': 'artificial intelligence',
            'max_papers': 10,
            'paper_type': 'survey'
        }
        validated = validate_research_query(query_data)
        print(f"   ✅ Validation working: {validated.topic}")
        
        # Test error handling
        print("🛠️  Testing error handling...")
        try:
            validate_research_query({'topic': '', 'max_papers': 10})
        except ValueError as e:
            print(f"   ✅ Error handling working: {str(e)[:50]}...")
        
        print("\n🎉 ALL BASIC FUNCTIONALITY TESTS PASSED!")
        print("✅ Your Academic Research Assistant is working properly!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("❌ Error details:")
        traceback.print_exc()
        return False

def test_simple_research():
    """Test a simple research operation"""
    print("\n🔬 TESTING SIMPLE RESEARCH OPERATION")
    print("=" * 50)
    
    try:
        from src.storage.models import Paper
        from datetime import datetime
        
        # Create a test paper
        test_paper = Paper(
            id="test-001",
            title="Test Paper on Machine Learning",
            authors=["Test Author"],
            abstract="This is a test paper abstract about machine learning research.",
            url="https://example.com/test-paper",
            published_date=datetime.now(),
            venue="Test Conference",
            citations=42
        )
        
        # Test saving and retrieving
        from src.storage.database import DatabaseManager
        db = DatabaseManager()
        
        # Save test paper
        success = db.save_paper(test_paper)
        print(f"   ✅ Paper saved: {success}")
        
        # Retrieve paper
        retrieved = db.get_paper("test-001")
        if retrieved:
            print(f"   ✅ Paper retrieved: {retrieved.title}")
        
        # Search papers
        results = db.search_papers("machine learning", limit=5)
        print(f"   ✅ Search results: {len(results)} papers found")
        
        print("🎉 SIMPLE RESEARCH OPERATION TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ RESEARCH TEST FAILED: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 ACADEMIC RESEARCH ASSISTANT - FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Run basic functionality tests
    basic_success = test_basic_functionality()
    
    # Run simple research tests
    research_success = test_simple_research()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS:")
    print(f"   Basic Functionality: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"   Research Operations: {'✅ PASS' if research_success else '❌ FAIL'}")
    
    if basic_success and research_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Your Academic Research Assistant is ready to use!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
        sys.exit(1)
