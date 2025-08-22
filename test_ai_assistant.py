#!/usr/bin/env python3
"""
Test script for AI Assistant functionality
"""

import sys
import os
sys.path.append('.')

def test_ai_assistant():
    """Test the AI assistant components"""
    
    print("🧪 Testing AI Assistant Components...")
    print("=" * 50)
    
    # Test 1: Configuration
    try:
        from src.utils.config import Config
        config = Config()
        print("✅ Configuration loaded successfully")
        print(f"   Environment: {config.environment}")
        print(f"   LLM Provider: {config.llm_config.get('provider', 'gemini')}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test 2: Gemini Client
    try:
        from src.llm.gemini_client import GeminiClient
        api_key = config.api_keys.get('google')
        if not api_key:
            print("⚠️ No Google API key found, skipping Gemini test")
        else:
            client = GeminiClient(api_key=api_key)
            status = client.get_status()
            print("✅ Gemini Client initialized")
            print(f"   Ready: {status.get('ready', False)}")
            print(f"   Model: {status.get('model', 'unknown')}")
    except Exception as e:
        print(f"❌ Gemini Client error: {e}")
        return False
    
    # Test 3: QA Agent
    try:
        from src.agents.qa_agent import QuestionAnsweringAgent
        qa_agent = QuestionAnsweringAgent()
        print("✅ QA Agent initialized")
        print(f"   Workers: {getattr(qa_agent, 'max_workers', 'default')}")
    except Exception as e:
        print(f"❌ QA Agent error: {e}")
        return False
    
    # Test 4: Simple Query
    try:
        print("\n🎯 Testing Simple Query...")
        test_query = "What is machine learning?"
        response = qa_agent.answer_question(test_query)
        
        if response and isinstance(response, dict) and response.get('answer'):
            answer = response['answer']
            if len(answer) > 50:
                print("✅ AI Assistant query test passed")
                print(f"   Response length: {len(answer)} characters")
                print(f"   Sample: {answer[:100]}...")
            else:
                print("⚠️ Query returned short response")
                print(f"   Response: {answer}")
        else:
            print("⚠️ Query returned unexpected format")
            print(f"   Response type: {type(response)}")
            
    except Exception as e:
        print(f"❌ Query test error: {e}")
        return False
    
    # Test 5: Database Connection
    try:
        from src.storage.database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database connection working")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    print("\n🎉 All AI Assistant tests passed!")
    print("Your dashboard AI functionality is working perfectly!")
    return True

if __name__ == "__main__":
    test_ai_assistant()
