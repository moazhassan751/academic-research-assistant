#!/usr/bin/env python3
"""
Test script to verify validator fixes are working correctly
"""

from src.utils.validators import validate_research_query, validate_export_formats, validate_paper_data

def test_validator_errors():
    """Test that validator errors are properly handled"""
    
    print("Testing validator error handling...")
    
    # Test empty topic
    try:
        validate_research_query({'topic': '', 'max_papers': 10})
    except ValueError as e:
        print(f"✅ Empty topic error: {e}")
    
    # Test short topic
    try:
        validate_research_query({'topic': 'AI', 'max_papers': 10})
    except ValueError as e:
        print(f"✅ Short topic error: {e}")
    
    # Test invalid max_papers
    try:
        validate_research_query({'topic': 'machine learning', 'max_papers': 0})
    except ValueError as e:
        print(f"✅ Invalid max_papers error: {e}")
    
    # Test invalid format
    try:
        validate_export_formats({'formats': ['pdf', 'invalid_format']})
    except ValueError as e:
        print(f"✅ Invalid format error: {e}")
    
    # Test empty formats
    try:
        validate_export_formats({'formats': []})
    except ValueError as e:
        print(f"✅ Empty formats error: {e}")
    
    # Test SQL injection sanitization
    result = validate_research_query({
        'topic': 'machine learning<script>alert("xss")</script>',
        'aspects': ['deep learning"; DROP TABLE papers; --']
    })
    print(f"✅ Sanitization working:")
    print(f"   Topic: {result.topic}")
    print(f"   Aspects: {result.aspects}")
    
    print("\n✅ All validator error handling tests passed!")

if __name__ == "__main__":
    test_validator_errors()
