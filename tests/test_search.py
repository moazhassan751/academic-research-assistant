import sys
sys.path.append('.')
from src.storage.database import db

# Test the search function directly
search_query = "automobile industry"
print(f"🔍 Testing search for: '{search_query}'")

try:
    results = db.search_papers(search_query, limit=10)
    print(f"✅ Search returned {len(results)} results")
    
    for i, paper in enumerate(results, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:2]) if paper.authors else 'Unknown'}")
        print(f"   Abstract: {paper.abstract[:100] if paper.abstract else 'No abstract'}...")
        
except Exception as e:
    print(f"❌ Search error: {e}")
    import traceback
    traceback.print_exc()

# Also test broader searches
print(f"\n🔍 Testing search for: 'automotive'")
try:
    results = db.search_papers("automotive", limit=5)
    print(f"✅ Search returned {len(results)} results")
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper.title[:60]}...")
except Exception as e:
    print(f"❌ Search error: {e}")
