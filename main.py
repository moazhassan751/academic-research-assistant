"""
Academic Research Assistant - Main CLI Interface
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from datetime import datetime, timedelta
from pathlib import Path

from src.crew.research_crew import ResearchCrew
from src.storage.database import db
from src.utils.config import config
from src.utils.logging import setup_logging, logger

# Initialize Rich console
console = Console()

def display_banner():
    """Display application banner"""
    banner = Text("🎓 Academic Research Assistant", style="bold blue")
    subtitle = Text("AI-Powered Literature Survey & Draft Generation", style="italic")
    
    panel = Panel(
        f"{banner}\n{subtitle}",
        title="Welcome",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)

def display_config_info():
    """Display current configuration"""
    env = config.environment
    llm_config = config.llm_config
    
    config_table = Table(title="Current Configuration", show_header=True)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Environment", env)
    config_table.add_row("LLM Provider", llm_config.get('provider', 'Unknown'))
    config_table.add_row("Model", llm_config.get('model', 'Unknown'))
    config_table.add_row("Database", str(Path(config.get('storage.database_path')).resolve()))
    
    console.print(config_table)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Academic Research Assistant - AI-powered literature survey tool"""
    ctx.ensure_object(dict)
    
    # Setup logging
    log_level = 'DEBUG' if verbose else 'INFO'
    setup_logging(log_level)
    
    # Display banner
    display_banner()

@cli.command()
def config_info():
    """Display current configuration"""
    display_config_info()

@cli.command()
def stats():
    """Display database statistics"""
    try:
        stats = db.get_stats()
        
        stats_table = Table(title="Database Statistics", show_header=True)
        stats_table.add_column("Entity", style="cyan")
        stats_table.add_column("Count", style="green", justify="right")
        
        stats_table.add_row("Papers", str(stats.get('papers', 0)))
        stats_table.add_row("Research Notes", str(stats.get('notes', 0)))
        stats_table.add_row("Themes", str(stats.get('themes', 0)))
        stats_table.add_row("Citations", str(stats.get('citations', 0)))
        
        console.print(stats_table)
        
    except Exception as e:
        console.print(f"[red]Error getting stats: {e}[/red]")

@cli.command()
@click.argument('topic')
@click.option('--aspects', '-a', multiple=True, help='Specific aspects to focus on')  
@click.option('--max-papers', '-n', default=50, help='Maximum number of papers to collect')
@click.option('--paper-type', '-t', default='survey', 
              type=click.Choice(['survey', 'review', 'analysis']), 
              help='Type of paper to generate')
@click.option('--recent-only', '-r', is_flag=True, 
              help='Only include papers from last 2 years')
@click.option('--output-dir', '-o', help='Output directory for results')
@click.option('--save-results', '-s', is_flag=True, default=True,
              help='Save results to files')
def research(topic, aspects, max_papers, paper_type, recent_only, output_dir, save_results):
    """Conduct comprehensive research on a topic"""
    
    # Validate inputs
    if not topic.strip():
        console.print("[red]Error: Research topic cannot be empty[/red]")
        return
    
    if max_papers > 200:
        console.print("[yellow]Warning: Large number of papers may take significant time[/yellow]")
        if not Confirm.ask("Continue anyway?"):
            return
    
    # Prepare parameters
    date_from = datetime.now() - timedelta(days=730) if recent_only else None
    aspects_list = list(aspects) if aspects else None
    
    console.print(Panel(
        f"[bold]Research Topic:[/bold] {topic}\n"
        f"[bold]Aspects:[/bold] {', '.join(aspects_list) if aspects_list else 'General'}\n"
        f"[bold]Max Papers:[/bold] {max_papers}\n"
        f"[bold]Paper Type:[/bold] {paper_type}\n"
        f"[bold]Recent Only:[/bold] {'Yes' if recent_only else 'No'}",
        title="Research Parameters",
        border_style="green"
    ))
    
    if not Confirm.ask("Proceed with research?"):
        return
    
    # Initialize research crew
    crew = ResearchCrew()
    
    # Execute research with progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        # Overall progress
        overall_task = progress.add_task("Research Progress", total=5)
        
        try:
            progress.update(overall_task, description="Starting research workflow...")
            
            # Execute the research workflow
            results = crew.execute_research_workflow(
                research_topic=topic,
                specific_aspects=aspects_list,
                max_papers=max_papers,
                paper_type=paper_type,
                date_from=date_from
            )
            
            progress.update(overall_task, advance=5, description="Research completed!")
            
            if not results.get('success'):
                console.print(f"[red]Research failed: {results.get('error', 'Unknown error')}[/red]")
                return
            
            # Display results summary
            display_research_results(results)
            
            # Save results if requested
            if save_results:
                output_path = crew.save_results(results, output_dir)
                console.print(f"\n[green]✅ Results saved to: {output_path}[/green]")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Research interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error during research: {e}[/red]")
            logger.error(f"Research error: {e}", exc_info=True)

def display_research_results(results):
    """Display comprehensive research results"""
    stats = results.get('statistics', {})
    
    # Summary table
    summary_table = Table(title="Research Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green", justify="right")
    
    summary_table.add_row("Execution Time", results.get('execution_time', 'Unknown'))
    summary_table.add_row("Papers Found", str(stats.get('papers_found', 0)))
    summary_table.add_row("Notes Extracted", str(stats.get('notes_extracted', 0)))
    summary_table.add_row("Themes Identified", str(stats.get('themes_identified', 0)))
    summary_table.add_row("Research Gaps", str(stats.get('gaps_identified', 0)))
    summary_table.add_row("Citations Generated", str(stats.get('citations_generated', 0)))
    
    console.print(summary_table)
    
    # Top papers
    if 'papers' in results and results['papers']:
        console.print("\n[bold cyan]📚 Top Papers Found:[/bold cyan]")
        for i, paper in enumerate(results['papers'][:5], 1):
            year = paper.published_date.year if paper.published_date else 'N/A'
            console.print(f"{i}. {paper.title} ({year})")
            console.print(f"   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
    
    # Research themes
    if 'themes' in results and results['themes']:
        console.print("\n[bold cyan]🎯 Key Research Themes:[/bold cyan]")
        for i, theme in enumerate(results['themes'][:5], 1):
            console.print(f"{i}. [bold]{theme.title}[/bold]")
            console.print(f"   {theme.description[:100]}...")
            console.print(f"   Frequency: {theme.frequency}, Confidence: {theme.confidence:.2f}")
    
    # Research gaps
    if 'gaps' in results and results['gaps']:
        console.print("\n[bold cyan]🔍 Research Gaps Identified:[/bold cyan]")
        for i, gap in enumerate(results['gaps'][:5], 1):
            console.print(f"{i}. {gap}")

@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=20, help='Number of results to show')
def search_papers(query, limit):
    """Search papers in the database"""
    try:
        papers = db.search_papers(query, limit)
        
        if not papers:
            console.print(f"[yellow]No papers found for query: {query}[/yellow]")
            return
        
        papers_table = Table(title=f"Search Results for '{query}'", show_header=True)
        papers_table.add_column("Title", style="cyan", max_width=50)
        papers_table.add_column("Authors", style="green", max_width=30)
        papers_table.add_column("Year", style="yellow", justify="center")
        papers_table.add_column("Citations", style="red", justify="right")
        
        for paper in papers:
            authors_str = ', '.join(paper.authors[:2])
            if len(paper.authors) > 2:
                authors_str += f" +{len(paper.authors)-2}"
            
            year = str(paper.published_date.year) if paper.published_date else 'N/A'
            
            papers_table.add_row(
                paper.title[:47] + "..." if len(paper.title) > 50 else paper.title,
                authors_str,
                year,
                str(paper.citations)
            )
        
        console.print(papers_table)
        console.print(f"\n[green]Found {len(papers)} papers[/green]")
        
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")

@cli.command()
@click.option('--min-frequency', '-f', default=2, help='Minimum theme frequency')
def list_themes(min_frequency):
    """List research themes in the database"""
    try:
        themes = db.get_themes(min_frequency)
        
        if not themes:
            console.print(f"[yellow]No themes found with frequency >= {min_frequency}[/yellow]")
            return
        
        themes_table = Table(title="Research Themes", show_header=True)
        themes_table.add_column("Title", style="cyan", max_width=40)
        themes_table.add_column("Description", style="green", max_width=50)
        themes_table.add_column("Frequency", style="yellow", justify="right")
        themes_table.add_column("Confidence", style="red", justify="right")
        
        for theme in themes:
            desc = theme.description[:47] + "..." if len(theme.description) > 50 else theme.description
            
            themes_table.add_row(
                theme.title,
                desc,
                str(theme.frequency),
                f"{theme.confidence:.2f}"
            )
        
        console.print(themes_table)
        console.print(f"\n[green]Found {len(themes)} themes[/green]")
        
    except Exception as e:
        console.print(f"[red]Error listing themes: {e}[/red]")

@cli.command()
@click.option('--backup-path', '-b', help='Backup file path')
def backup_db(backup_path):
    """Backup the research database"""
    try:
        import shutil
        from datetime import datetime
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backup_research_db_{timestamp}.db"
        
        # Ensure backup directory exists
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Copy database file
        shutil.copy2(db.db_path, backup_path)
        
        console.print(f"[green]✅ Database backed up to: {backup_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Backup error: {e}[/red]")

@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear all data?')
def clear_db():
    """Clear all data from the database (use with caution!)"""
    try:
        # Drop and recreate tables
        db.db.executescript("""
            DROP TABLE IF EXISTS papers;
            DROP TABLE IF EXISTS research_notes;
            DROP TABLE IF EXISTS research_themes;
            DROP TABLE IF EXISTS citations;
        """)
        
        # Reinitialize
        db._initialize_tables()
        
        console.print("[green]✅ Database cleared successfully[/green]")
        
    except Exception as e:
        console.print(f"[red]Error clearing database: {e}[/red]")

@cli.command()
def interactive():
    """Start interactive research session"""
    console.print("[bold green]🚀 Interactive Research Session Started[/bold green]")
    console.print("Type 'help' for available commands or 'exit' to quit.\n")
    
    crew = ResearchCrew()
    
    while True:
        try:
            command = Prompt.ask("\n[cyan]research>[/cyan]", default="help")
            
            if command.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            elif command.lower() == 'help':
                console.print("""
[bold cyan]Available Commands:[/bold cyan]
- [green]research <topic>[/green] - Start research on a topic
- [green]stats[/green] - Show database statistics  
- [green]search <query>[/green] - Search papers in database
- [green]themes[/green] - List research themes
- [green]clear[/green] - Clear screen
- [green]exit[/green] - Exit interactive mode
""")
            
            elif command.lower() == 'stats':
                stats = db.get_stats()
                for key, value in stats.items():
                    console.print(f"[cyan]{key.title()}:[/cyan] {value}")
            
            elif command.lower() == 'clear':
                console.clear()
                display_banner()
            
            elif command.lower().startswith('search '):
                query = command[7:].strip()
                if query:
                    papers = db.search_papers(query, 10)
                    console.print(f"Found {len(papers)} papers for '{query}'")
                    for paper in papers[:5]:
                        console.print(f"- {paper.title}")
                else:
                    console.print("[red]Please provide a search query[/red]")
            
            elif command.lower().startswith('research '):
                topic = command[9:].strip()
                if topic:
                    console.print(f"[green]Starting research on: {topic}[/green]")
                    results = crew.execute_research_workflow(topic, max_papers=20)
                    if results.get('success'):
                        display_research_results(results)
                    else:
                        console.print(f"[red]Research failed: {results.get('error')}[/red]")
                else:
                    console.print("[red]Please provide a research topic[/red]")
            
            elif command.lower() == 'themes':
                themes = db.get_themes(1)
                console.print(f"Found {len(themes)} themes:")
                for theme in themes[:10]:
                    console.print(f"- [bold]{theme.title}[/bold] (freq: {theme.frequency})")
            
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == '__main__':
    cli()