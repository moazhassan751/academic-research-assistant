#!/usr/bin/env python3
"""Test QA Agent efficiency and functionality"""

import sys
import time
sys.path.append('.')

from src.agents.qa_agent import QuestionAnsweringAgent

def test_qa_agent_efficiency():
    print("Testing QA Agent efficiency...")
    
    # Initialize agent with timing
    print("Initializing QA Agent...")
    start_time = time.time()
    qa_agent = QuestionAnsweringAgent()
    init_time = time.time() - start_time
    print(f"✓ QA Agent initialized in {init_time:.2f} seconds")
    
    # Test question answering with a research question
    test_question = "What are the main challenges in electric vehicle battery technology?"
    print(f"Testing question: {test_question}")
    
    try:
        # Test the answer_question method with timing
        print("Generating answer...")
        answer_start = time.time()
        result = qa_agent.answer_question(test_question, research_topic="electric vehicles")
        answer_time = time.time() - answer_start
        print(f"✓ Answer generation completed in {answer_time:.2f} seconds")
        
        # Check the result structure
        if isinstance(result, dict):
            print(f"Answer keys: {list(result.keys())}")
            if "answer" in result:
                answer_length = len(result["answer"])
                print(f"Answer length: {answer_length} characters")
                if answer_length > 100:
                    print("Answer preview:", result["answer"][:200] + "...")
                else:
                    print("Full answer:", result["answer"])
            if "sources" in result:
                print(f"Sources found: {len(result['sources'])}")
            if "confidence" in result:
                print(f"Confidence: {result['confidence']}")
            if "question_type" in result:
                print(f"Question type: {result['question_type']}")
        else:
            print(f"Result type: {type(result)}")
            print(f"Result preview: {str(result)[:200]}...")
            
        # Test performance stats
        print("\nPerformance Statistics:")
        stats = qa_agent.get_performance_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Error during question answering: {e}")
        import traceback
        traceback.print_exc()
    
    print("QA Agent test completed")

if __name__ == "__main__":
    test_qa_agent_efficiency()
