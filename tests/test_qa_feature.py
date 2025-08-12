#!/usr/bin/env python3
"""
Test script for the new Q&A feature
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crew.research_crew import ResearchCrew
from src.utils.logging import setup_logging, logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

def test_qa_feature():
    """Test the Q&A feature with sample questions"""
    
    console = Console()
    
    # Setup logging
    setup_logging()
    
    console.print(Panel(
        Text("🧪 Testing Q&A Feature", style="bold blue"),
        title="Academic Research Assistant - Q&A Test",
        border_style="blue"
    ))
    
    try:
        # Initialize research crew
        console.print("🔄 Initializing research crew...")
        crew = ResearchCrew()
        console.print("✅ Research crew initialized successfully!")
        
        # Test questions
        test_questions = [
            {
                "question": "What are the recent trends and challenges in transformer-based architectures for vision tasks?",
                "topic": "computer vision transformers"
            },
            {
                "question": "How does machine learning improve healthcare outcomes?",
                "topic": "machine learning healthcare"
            },
            {
                "question": "What are the main challenges in quantum computing research?",
                "topic": "quantum computing"
            }
        ]
        
        for i, test_case in enumerate(test_questions, 1):
            console.print(f"\n{'='*80}")
            console.print(f"📋 Test {i}/3: {test_case['question']}")
            console.print(f"{'='*80}")
            
            try:
                # Answer the question
                console.print("🔍 Searching for relevant papers and generating answer...")
                result = crew.answer_question(
                    question=test_case['question'],
                    research_topic=test_case['topic']
                )
                
                # Display results
                console.print(f"\n📊 **Results Summary:**")
                console.print(f"  • Papers found: {result.get('paper_count', 0)}")
                console.print(f"  • Confidence score: {result.get('confidence', 0):.2f}")
                console.print(f"  • Sources used: {result.get('top_papers_used', 0)}")
                
                console.print(f"\n📝 **Answer:**")
                answer = result.get('answer', 'No answer generated')
                # Truncate long answers for display
                if len(answer) > 500:
                    console.print(answer[:500] + "... [truncated]")
                else:
                    console.print(answer)
                
                # Show sources
                sources = result.get('sources', [])
                if sources:
                    console.print(f"\n📚 **Top Sources:**")
                    for j, source in enumerate(sources[:3], 1):
                        console.print(f"  {j}. {source.get('title', 'Unknown Title')}")
                        console.print(f"     Authors: {source.get('authors', 'Unknown')}")
                        console.print(f"     Relevance: {source.get('relevance_score', 0):.3f}")
                
                # Test follow-up questions
                console.print(f"\n🔄 Testing follow-up questions...")
                follow_ups = crew.qa_agent.get_follow_up_questions(test_case['question'], result)
                if follow_ups:
                    console.print(f"💡 **Suggested follow-up questions:**")
                    for j, follow_up in enumerate(follow_ups[:3], 1):
                        console.print(f"  {j}. {follow_up}")
                else:
                    console.print("⚠️  No follow-up questions generated")
                
                console.print("✅ Test completed successfully!")
                
            except Exception as e:
                console.print(f"❌ Test {i} failed: {str(e)}")
                logger.error(f"Test {i} error: {e}", exc_info=True)
                continue
        
        console.print(f"\n{'='*80}")
        console.print("🎉 Q&A Feature testing completed!")
        console.print(f"{'='*80}")
        
    except Exception as e:
        console.print(f"❌ Failed to initialize test: {str(e)}")
        logger.error(f"Test initialization error: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    success = test_qa_feature()
    sys.exit(0 if success else 1)
