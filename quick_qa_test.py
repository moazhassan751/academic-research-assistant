#!/usr/bin/env python3
"""
Quick validation test for the QA agent improvements
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.qa_agent import QuestionAnsweringAgent
from src.utils.logging import logger

async def test_qa_improvements():
    """Test the key improvements we made"""
    print("Testing QA Agent Improvements...")
    print("=" * 50)
    
    # Initialize QA agent
    qa_agent = QuestionAnsweringAgent()
    
    # Test questions
    test_questions = [
        "What are the latest trends in machine learning?",
        "How do neural networks work?",
        "What is artificial intelligence?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\nTest {i}: {question}")
        print("-" * 40)
        
        try:
            result = await qa_agent.answer_question_async(question)
            
            print(f"Answer: {result['answer'][:100]}...")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Source Papers: {len(result.get('source_papers', []))}")
            print(f"Question Type: {result.get('question_type', 'unknown')}")
            
            # Check if improvements are working
            if result['confidence'] > 0.2:
                print("✅ Confidence above threshold")
            else:
                print("❌ Confidence below threshold")
                
            if len(result.get('source_papers', [])) > 0:
                print("✅ Papers retrieved successfully")
            else:
                print("❌ No papers retrieved")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("QA Agent Improvement Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_qa_improvements())
