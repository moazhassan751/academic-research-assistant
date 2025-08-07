#!/usr/bin/env python3
"""
Quick test script for OpenAlex Tool
Run this from your project root to test the fixed OpenAlex integration
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / "src"))

def test_openalex():
    """Test OpenAlex tool functionality"""
    try:
        from src.tools.Open_Alex_tool import OpenAlexTool
        
        print("🔧 Testing OpenAlex Tool...")
        
        tool = OpenAlexTool(mailto="rmoazhassan555@gmail.com")

        print("\n1. Testing search_papers()...")
        papers = tool.search_papers("machine learning", max_results=3)
        print(f"✅ Search returned {len(papers)} papers")
        
        if papers:
            print("\n📄 First paper details:")
            paper = papers[0]  # This is a Paper object, not a dict
            print(f"  Title: {paper.title}")
            print(f"  Authors: {', '.join(paper.authors) if paper.authors else 'No authors'}")
            print(f"  Citations: {paper.citations}")
            print(f"  Venue: {paper.venue or 'N/A'}")
            print(f"  DOI: {paper.doi or 'N/A'}")
            print(f"  Published: {paper.published_date or 'N/A'}")
            print(f"  Abstract: {paper.abstract[:200] + '...' if paper.abstract and len(paper.abstract) > 200 else paper.abstract}")
            print(f"  URL: {paper.url or 'N/A'}")
        
        print("\n2. Testing search_by_author()...")
        # Try a simpler author name first
        author_papers = tool.search_by_author("Hinton", max_results=2)
        print(f"✅ Author search returned {len(author_papers)} papers")
        
        if author_papers:
            print(f"  First paper by Hinton: {author_papers[0].title}")
        else:
            # If that fails, try a different approach
            print("  Trying alternative author search...")
            author_papers = tool.search_by_author("Geoffrey E. Hinton", max_results=2)
            if author_papers:
                print(f"  Found {len(author_papers)} papers with full name")
        
        print("\n3. Testing search_by_doi()...")
        # Use a known DOI for testing
        test_doi = "10.1038/nature14539"  # DeepMind Nature paper
        doi_paper = tool.search_by_doi(test_doi)
        if doi_paper:
            print(f"✅ DOI search found: {doi_paper.title}")
        else:
            print("⚠️ DOI search returned no results (may not be in OpenAlex)")
        
        print("\n🎉 All tests completed successfully!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory.")
        print("Also ensure your src/storage/models.py contains the Paper class.")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_openalex()
    sys.exit(0 if success else 1)