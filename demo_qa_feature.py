#!/usr/bin/env python3
"""
Demonstration script for the Academic Research Assistant Q&A feature
This shows how users can ask questions about transformer-based architectures for vision tasks
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.crew.research_crew import ResearchCrew
from src.storage.database import db

console = Console()

def demonstrate_qa_feature():
    """Demonstrate the Q&A feature with transformer vision examples"""
    
    console.print(Panel(
        "[bold blue]🚀 Academic Research Assistant - Q&A Feature Demo[/bold blue]\n\n"
        "This demonstration shows how to ask questions about research papers\n"
        "and get AI-powered answers with citations and follow-up suggestions.",
        title="Demo: Question Answering Feature",
        border_style="blue"
    ))
    
    # Initialize research crew
    console.print("[cyan]🔧 Initializing research crew...[/cyan]")
    crew = ResearchCrew()
    
    # Check database status
    stats = db.get_stats()
    paper_count = stats.get('papers', 0)
    
    console.print(f"[green]📚 Database contains {paper_count} papers[/green]")
    
    if paper_count == 0:
        console.print(Panel(
            "[yellow]⚠️ No papers in database![/yellow]\n\n"
            "To demonstrate the Q&A feature effectively, you should first\n"
            "collect some papers by running:\n\n"
            "[bold]python main.py research 'transformer vision'[/bold]\n"
            "[bold]python main.py research 'computer vision'[/bold]\n\n"
            "For now, we'll show you how the feature works conceptually.",
            title="Database Setup Needed",
            border_style="yellow"
        ))
    
    # Demo questions about transformer-based architectures for vision
    demo_questions = [
        "What are the recent trends and challenges in transformer-based architectures for vision tasks?",
        "How do Vision Transformers (ViTs) compare to traditional CNNs in terms of performance?",
        "What are the main limitations of applying transformers to computer vision?",
        "Which hybrid approaches combine transformers with convolutional neural networks?",
        "What are the computational challenges of using transformers for image processing?"
    ]
    
    console.print("\n[bold cyan]🎯 Demo Questions About Transformer Vision:[/bold cyan]")
    
    for i, question in enumerate(demo_questions, 1):
        console.print(f"\n[bold blue]Question {i}:[/bold blue]")
        console.print(f"[italic]'{question}'[/italic]")
        
        try:
            # Simulate the Q&A process
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("🔍 Analyzing papers and generating answer...", total=None)
                
                # Answer the question
                result = crew.answer_research_question(
                    question=question,
                    research_topic="transformer vision",  # Focus on relevant papers
                    paper_limit=15
                )
                
                progress.update(task, completed=True)
            
            # Display results
            display_qa_result(result, question, i)
            
            # Pause between questions for readability
            if i < len(demo_questions):
                console.input("\n[dim]Press Enter to continue to the next question...[/dim]")
        
        except Exception as e:
            console.print(f"[red]❌ Error processing question {i}: {e}[/red]")
            continue
    
    # Show how to use the feature
    console.print(Panel(
        "[bold green]✅ Demo Complete![/bold green]\n\n"
        "[bold]How to use the Q&A feature:[/bold]\n\n"
        "1. [yellow]Collect papers first:[/yellow]\n"
        "   python main.py research 'your topic'\n\n"
        "2. [yellow]Ask single questions:[/yellow]\n"
        "   python main.py ask 'your question' --topic 'filter topic'\n\n"
        "3. [yellow]Start interactive sessions:[/yellow]\n"
        "   python main.py qa-session --topic 'focus topic'\n\n"
        "4. [yellow]Use in interactive mode:[/yellow]\n"
        "   python main.py interactive\n"
        "   > ask What are the latest developments in AI?\n\n"
        "[bold]Key Features:[/bold]\n"
        "• AI-powered answers with confidence scores\n"
        "• Automatic source citation and relevance ranking\n"
        "• Follow-up question suggestions\n"
        "• Topic-based filtering\n"
        "• Session saving and export options",
        title="🎓 How to Use Q&A Feature",
        border_style="green"
    ))

def display_qa_result(result, question, question_num):
    """Display a Q&A result in a formatted way"""
    
    answer = result.get('answer', 'No answer available')
    confidence = result.get('confidence', 0.0)
    paper_count = result.get('paper_count', 0)
    sources = result.get('sources', [])
    follow_ups = result.get('follow_up_questions', [])
    
    # Determine color scheme based on confidence
    if confidence >= 0.7:
        confidence_color = "green"
        border_color = "green"
        emoji = "🎯"
    elif confidence >= 0.4:
        confidence_color = "yellow"
        border_color = "yellow"
        emoji = "🤔"
    else:
        confidence_color = "red"
        border_color = "red"
        emoji = "❓"
    
    # Display answer
    console.print(Panel(
        answer,
        title=f"{emoji} Answer {question_num} (Confidence: [{confidence_color}]{confidence:.2f}[/{confidence_color}], Papers: {paper_count})",
        border_style=border_color
    ))
    
    # Show sources if available
    if sources and len(sources) > 0:
        console.print(f"\n[bold cyan]📚 Sources Used ({len(sources)} papers):[/bold cyan]")
        
        sources_table = Table(show_header=True, header_style="bold blue")
        sources_table.add_column("Paper", max_width=35)
        sources_table.add_column("Authors", max_width=20)
        sources_table.add_column("Relevance", justify="right")
        sources_table.add_column("Citations", justify="right")
        
        for source in sources[:5]:  # Show top 5 sources
            title = source.get('title', 'Unknown')
            authors = source.get('authors', 'Unknown')
            relevance = f"{source.get('relevance_score', 0):.2f}"
            citations = str(source.get('citations', 0))
            
            # Truncate long titles and authors
            if len(title) > 32:
                title = title[:29] + "..."
            if len(authors) > 17:
                authors = authors[:14] + "..."
            
            sources_table.add_row(title, authors, relevance, citations)
        
        console.print(sources_table)
    else:
        console.print("[yellow]⚠️ No sources available - this might indicate limited papers in database[/yellow]")
    
    # Show follow-up questions
    if follow_ups:
        console.print(f"\n[bold cyan]💡 Follow-up Questions You Could Ask:[/bold cyan]")
        for i, fq in enumerate(follow_ups[:3], 1):
            console.print(f"   {i}. {fq}")
    
    # Show performance info
    exec_time = result.get('execution_time', 'Unknown')
    console.print(f"\n[dim]⏱️ Answered in {exec_time}[/dim]")

def show_feature_comparison():
    """Show how the Q&A feature compares to traditional search"""
    
    console.print("\n" + "="*60)
    console.print(Panel(
        "[bold]🔄 Traditional Search vs. AI Q&A[/bold]\n\n"
        "[red]Traditional Database Search:[/red]\n"
        "• Returns list of papers matching keywords\n"
        "• User must read through papers manually\n"
        "• No synthesis or analysis\n"
        "• Limited by exact keyword matching\n\n"
        "[green]AI-Powered Q&A:[/green]\n"
        "• Analyzes paper content and provides direct answers\n"
        "• Synthesizes information from multiple sources\n"
        "• Provides confidence scores and relevance ranking\n"
        "• Understands context and semantic meaning\n"
        "• Suggests follow-up questions\n"
        "• Cites sources automatically",
        title="Feature Comparison",
        border_style="blue"
    ))

def main():
    """Run the Q&A feature demonstration"""
    
    try:
        # Show feature comparison
        show_feature_comparison()
        
        # Run the main demonstration
        demonstrate_qa_feature()
        
        console.print("\n[bold green]🎉 Thank you for trying the Academic Research Assistant Q&A feature![/bold green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Demo error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

if __name__ == "__main__":
    main()
