#!/usr/bin/env python3
"""
Simple QA agent test to identify hanging issues
"""
import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.storage.database import db
from src.utils.config import config
from src.llm.gemini_client import GeminiClient

def test_simple_qa():
    """Test basic QA functionality without complex async operations"""
    print("🔍 Testing Simple QA Agent...")
    
    try:
        # Initialize basic components
        print("1. Initializing database connection...")
        papers = db.get_recent_papers(limit=2)
        print(f"   Found {len(papers)} papers in database")
        
        if not papers:
            print("   No papers found - testing with sample question")
            return test_without_papers()
        
        # Initialize LLM client
        print("2. Initializing Gemini client...")
        llm_config = config.llm_config
        llm = GeminiClient(
            api_key=llm_config.get('api_key'),
            model=llm_config.get('model', 'gemini-2.5-flash')
        )
        
        # Test simple question answering
        print("3. Testing basic QA...")
        question = "What is artificial intelligence?"
        
        # Create simple context from papers
        context = ""
        for paper in papers[:2]:
            title = getattr(paper, 'title', 'No title') or 'No title'
            abstract = getattr(paper, 'abstract', 'No abstract available') or 'No abstract available'
            if len(abstract) > 200:
                abstract = abstract[:200] + "..."
            context += f"Title: {title}\nAbstract: {abstract}\n\n"
        
        # Simple prompt
        prompt = f"""Based on the following research papers, please answer this question: {question}

Research Papers:
{context}

Please provide a clear, concise answer based on the available information."""
        
        print("4. Generating response...")
        start_time = time.time()
        response = llm.generate(prompt)
        end_time = time.time()
        
        print(f"✅ QA Test Completed in {end_time - start_time:.2f} seconds")
        print(f"📄 Answer: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ QA Test Failed: {e}")
        return False

def test_without_papers():
    """Test QA without database papers"""
    try:
        print("   Testing without database papers...")
        llm_config = config.llm_config
        llm = GeminiClient(
            api_key=llm_config.get('api_key'),
            model=llm_config.get('model', 'gemini-2.5-flash')
        )
        
        question = "What is machine learning?"
        simple_prompt = f"Please provide a brief explanation of: {question}"
        
        start_time = time.time()
        response = llm.generate(simple_prompt)
        end_time = time.time()
        
        print(f"✅ Simple QA Test Completed in {end_time - start_time:.2f} seconds")
        print(f"📄 Answer: {response[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Simple QA Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Simple QA Agent Test...")
    success = test_simple_qa()
    
    if success:
        print("\n✅ Simple QA test passed!")
        print("The issue is likely in the complex async/threading architecture.")
    else:
        print("\n❌ Simple QA test failed!")
        print("The issue might be with basic LLM or database connectivity.")
