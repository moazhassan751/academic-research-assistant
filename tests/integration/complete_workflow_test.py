#!/usr/bin/env python3
"""
Complete workflow test: Research a topic and then ask questions about it
"""
import sys
from pathlib import Path
import time

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crew.research_crew import ResearchCrew
from src.storage.database import db
from src.utils.logging import setup_logging, logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm

def run_complete_workflow():
    """Run the complete research workflow followed by Q&A"""
    
    console = Console()
    
    # Setup logging
    setup_logging()
    
    console.print(Panel(
        Text("🔬 Complete Research & Q&A Workflow Test", style="bold blue"),
        title="Academic Research Assistant - Full Test",
        border_style="blue"
    ))
    
    try:
        # Initialize research crew
        console.print("🔄 Initializing research crew...")
        crew = ResearchCrew()
        console.print("✅ Research crew initialized successfully!")
        
        # Step 1: Get research topic from user or use default
        console.print("\n" + "="*80)
        console.print("📚 STEP 1: Research Phase")
        console.print("="*80)
        
        # Predefined research topics to choose from
        default_topics = [
            "transformer architectures in computer vision",
            "federated learning applications",
            "quantum machine learning",
            "explainable AI methods",
            "neural architecture search"
        ]
        
        console.print("Choose a research topic:")
        for i, topic in enumerate(default_topics, 1):
            console.print(f"  {i}. {topic}")
        console.print("  6. Custom topic")
        
        choice = Prompt.ask("Select option", choices=[str(i) for i in range(1, 7)], default="1")
        
        if choice == "6":
            research_topic = Prompt.ask("Enter your research topic")
        else:
            research_topic = default_topics[int(choice) - 1]
        
        max_papers = int(Prompt.ask("Maximum papers to collect", default="20"))
        
        console.print(f"\n🎯 Research Topic: {research_topic}")
        console.print(f"📊 Max Papers: {max_papers}")
        
        if not Confirm.ask("Proceed with research?"):
            console.print("❌ Research cancelled")
            return
        
        # Execute research
        console.print("\n🔍 Starting research workflow...")
        start_time = time.time()
        
        try:
            results = crew.execute_research_workflow(
                research_topic=research_topic,
                specific_aspects=None,
                max_papers=max_papers,
                paper_type='survey',
                date_from=None,
                progress_callback=lambda step, desc: console.print(f"📊 {desc}")
            )
            
            research_time = time.time() - start_time
            
            if not results.get('success'):
                console.print(f"❌ Research failed: {results.get('error', 'Unknown error')}")
                return
            
            console.print(f"✅ Research completed in {research_time:.2f} seconds!")
            
            # Display research summary
            stats = results.get('statistics', {})
            console.print(f"\n📈 Research Results:")
            console.print(f"  • Papers found: {stats.get('papers_found', 0)}")
            console.print(f"  • Notes extracted: {stats.get('notes_extracted', 0)}")
            console.print(f"  • Themes identified: {stats.get('themes_identified', 0)}")
            
            if stats.get('papers_found', 0) == 0:
                console.print("⚠️  No papers found. Cannot proceed with Q&A phase.")
                return
            
        except Exception as e:
            console.print(f"❌ Research failed: {e}")
            logger.error(f"Research error: {e}", exc_info=True)
            return
        
        # Step 2: Q&A Phase
        console.print("\n" + "="*80)
        console.print("❓ STEP 2: Question & Answer Phase")
        console.print("="*80)
        
        # Predefined questions related to the topic
        sample_questions = [
            f"What are the key findings in {research_topic}?",
            f"What are the main challenges in {research_topic}?",
            f"What are the recent advances in {research_topic}?",
            f"What are the future research directions in {research_topic}?",
            f"What methodologies are commonly used in {research_topic}?"
        ]
        
        console.print("Now let's ask questions about the retrieved papers!")
        console.print("\nSample questions you can ask:")
        for i, question in enumerate(sample_questions, 1):
            console.print(f"  {i}. {question}")
        
        # Interactive Q&A session
        question_count = 0
        max_questions = 3
        
        while question_count < max_questions:
            console.print(f"\n--- Question {question_count + 1}/{max_questions} ---")
            
            # Get question from user
            use_sample = Confirm.ask("Use a sample question?", default=True)
            
            if use_sample and question_count < len(sample_questions):
                question = sample_questions[question_count]
                console.print(f"Selected: {question}")
            else:
                question = Prompt.ask("Enter your question")
            
            if not question.strip():
                console.print("⚠️  Empty question, skipping...")
                continue
            
            # Answer the question
            console.print(f"\n🔍 Processing question: {question}")
            
            try:
                qa_start_time = time.time()
                answer_result = crew.answer_question(
                    question=question,
                    research_topic=research_topic,
                    paper_limit=15
                )
                qa_time = time.time() - qa_start_time
                
                console.print(f"\n📊 **Answer Summary:**")
                console.print(f"  • Processing time: {qa_time:.2f} seconds")
                console.print(f"  • Papers analyzed: {answer_result.get('paper_count', 0)}")
                console.print(f"  • Confidence score: {answer_result.get('confidence', 0):.2f}")
                console.print(f"  • Sources used: {answer_result.get('top_papers_used', 0)}")
                
                console.print(f"\n📝 **Answer:**")
                answer = answer_result.get('answer', 'No answer generated')
                
                # Display answer with proper formatting
                if len(answer) > 800:
                    console.print(answer[:800] + "... [truncated for display]")
                    show_full = Confirm.ask("Show full answer?", default=False)
                    if show_full:
                        console.print(f"\n**Full Answer:**\n{answer}")
                else:
                    console.print(answer)
                
                # Show top sources
                sources = answer_result.get('sources', [])
                if sources:
                    console.print(f"\n📚 **Top Sources:**")
                    for i, source in enumerate(sources[:3], 1):
                        console.print(f"  {i}. {source.get('title', 'Unknown Title')}")
                        console.print(f"     Authors: {source.get('authors', 'Unknown')}")
                        console.print(f"     Relevance: {source.get('relevance_score', 0):.3f}")
                
                # Show follow-up questions
                follow_ups = answer_result.get('follow_up_questions', [])
                if follow_ups:
                    console.print(f"\n💡 **Suggested follow-up questions:**")
                    for i, follow_up in enumerate(follow_ups[:3], 1):
                        console.print(f"  {i}. {follow_up}")
                
                question_count += 1
                
                if question_count < max_questions:
                    if not Confirm.ask("\nContinue with another question?", default=True):
                        break
                
            except Exception as e:
                console.print(f"❌ Error answering question: {e}")
                logger.error(f"Q&A error: {e}", exc_info=True)
                continue
        
        # Final Summary
        console.print("\n" + "="*80)
        console.print("🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        console.print("="*80)
        
        console.print(f"✅ Research Phase:")
        console.print(f"  • Topic: {research_topic}")
        console.print(f"  • Papers collected: {stats.get('papers_found', 0)}")
        console.print(f"  • Research time: {research_time:.2f} seconds")
        
        console.print(f"✅ Q&A Phase:")
        console.print(f"  • Questions answered: {question_count}")
        console.print(f"  • Average confidence: Various")
        
        console.print(f"\n📊 Total database statistics:")
        try:
            db_stats = db.get_stats()
            console.print(f"  • Total papers in DB: {db_stats.get('papers', 0)}")
            console.print(f"  • Total notes: {db_stats.get('notes', 0)}")
            console.print(f"  • Total themes: {db_stats.get('themes', 0)}")
        except Exception as e:
            console.print(f"  • Could not fetch DB stats: {e}")
        
        console.print(f"\n🎯 The workflow demonstrates:")
        console.print(f"  • Automatic paper collection from multiple sources")
        console.print(f"  • Intelligent note extraction and theme identification")
        console.print(f"  • Context-aware question answering")
        console.print(f"  • Source citation and relevance scoring")
        console.print(f"  • Follow-up question generation")
        
        console.print(f"\n💡 You can now use the CLI commands:")
        console.print(f"  • python main.py search-papers \"your query\"")
        console.print(f"  • python main.py --ask \"your question\"")
        console.print(f"  • python main.py stats")
        console.print(f"  • python main.py list-themes")
        
    except KeyboardInterrupt:
        console.print("\n⏹️ Workflow interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Workflow error: {e}", exc_info=True)

if __name__ == "__main__":
    run_complete_workflow()
