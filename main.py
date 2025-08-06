import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from datetime import datetime, timedelta
from pathlib import Path
import sys

try:
    from src.crew.research_crew import ResearchCrew
    from src.storage.database import db
    from src.utils.config import config
    from src.utils.logging import setup_logging, logger
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running from the project root directory and all dependencies are installed.")
    sys.exit(1)

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
    try:
        env = config.environment
        llm_config = config.llm_config
        
        config_table = Table(title="Current Configuration", show_header=True)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        
        config_table.add_row("Environment", env)
        config_table.add_row("LLM Provider", llm_config.get('provider', 'Unknown'))
        config_table.add_row("Model", llm_config.get('model', 'Unknown'))
        config_table.add_row("Database", str(Path(config.get('storage.database_path', 'data/research.db')).resolve()))
        
        console.print(config_table)
    except Exception as e:
        console.print(f"[red]Error displaying config: {e}[/red]")
        logger.error(f"Config display error: {e}", exc_info=True)

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
        with console.status("Fetching database statistics..."):
            stats = db.get_stats()
        
        stats_table = Table(title="Database Statistics", show_header=True)
        stats_table.add_column("Entity", style="cyan")
        stats_table.add_column("Count", style="green", justify="right")
        
        stats_table.add_row("Papers", str(stats.get('papers', 0)))
        stats_table.add_row("Research Notes", str(stats.get('notes', 0)))
        stats_table.add_row("Themes", str(stats.get('themes', 0)))
        stats_table.add_row("Citations", str(stats.get('citations', 0)))
        
        console.print(stats_table)
        
        if stats.get('papers', 0) == 0:
            console.print("\n[yellow]💡 No papers in database yet. Try running a research command to populate it.[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error getting stats: {e}[/red]")
        logger.error(f"Stats error: {e}", exc_info=True)

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
        console.print("[red]❌ Error: Research topic cannot be empty[/red]")
        return

    if len(topic) < 3:
        console.print("[red]❌ Error: Research topic too short (minimum 3 characters)[/red]")
        return
    
    if max_papers > 200:
        console.print("[yellow]⚠️ Warning: Large number of papers may take significant time[/yellow]")
        if not Confirm.ask("Continue anyway?"):
            return
    
    if max_papers < 5:
        console.print("[yellow]⚠️ Warning: Very few papers requested, results may be limited[/yellow]")
    
    # Prepare parameters
    date_from = datetime.now() - timedelta(days=730) if recent_only else None
    aspects_list = list(aspects) if aspects else None
    
    console.print(Panel(
        f"[bold]Research Topic:[/bold] {topic}\n"
        f"[bold]Aspects:[/bold] {', '.join(aspects_list) if aspects_list else 'General'}\n"
        f"[bold]Max Papers:[/bold] {max_papers}\n"
        f"[bold]Paper Type:[/bold] {paper_type}\n"
        f"[bold]Recent Only:[/bold] {'Yes' if recent_only else 'No'}\n"
        f"[bold]Save Results:[/bold] {'Yes' if save_results else 'No'}\n"
        f"[bold]Output Directory:[/bold] {output_dir or 'Default'}",
        title="Research Parameters",
        border_style="green"
    ))
    
    if not Confirm.ask("Proceed with research?"):
        console.print("[yellow]Research cancelled by user[/yellow]")
        return
    
    try:
        # Initialize research crew
        console.print("[cyan]🚀 Initializing research crew...[/cyan]")
        crew = ResearchCrew()
        
        # Execute research with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
            
            # Overall progress
            overall_task = progress.add_task("Research Progress", total=5)
            
            progress.update(overall_task, description="Starting research workflow...")
            
            # Execute the research workflow with progress callback
            results = crew.execute_research_workflow(
                research_topic=topic,
                specific_aspects=aspects_list,
                max_papers=max_papers,
                paper_type=paper_type,
                date_from=date_from,
                progress_callback=lambda step, desc: progress.update(
                    overall_task, 
                    advance=1, 
                    description=f"📊 {desc}"
                )
            )
            
            progress.update(overall_task, description="✅ Research completed!")
            
            if not results.get('success'):
                error_msg = results.get('error', 'Unknown error occurred')
                console.print(f"[red]❌ Research failed: {error_msg}[/red]")
                return
            
            # Display results summary
            display_research_results(results)
            
            # Save results if requested
            if save_results:
                console.print("\n[cyan]💾 Saving results...[/cyan]")
                output_path = crew.save_results(results, output_dir)
                console.print(f"[green]✅ Results saved to: {output_path}[/green]")
                
                # Show saved files
                if Path(output_path).exists():
                    files = list(Path(output_path).iterdir())
                    console.print(f"[blue]📁 Generated {len(files)} files:[/blue]")
                    for file in files[:5]:  # Show first 5 files
                        console.print(f"   - {file.name}")
                    if len(files) > 5:
                        console.print(f"   ... and {len(files) - 5} more files")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️ Research interrupted by user[/yellow]")
        console.print("Partial results may have been saved.")
    except Exception as e:
        console.print(f"\n[red]❌ Error during research: {e}[/red]")
        logger.error(f"Research error: {e}", exc_info=True)
        
        # Provide troubleshooting hints
        console.print("\n[yellow]💡 Troubleshooting tips:[/yellow]")
        console.print("   - Check your internet connection")
        console.print("   - Verify API keys are valid")
        console.print("   - Try reducing --max-papers")
        console.print("   - Run with --verbose for detailed logs")

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
    
    # Show quality indicators
    papers_found = stats.get('papers_found', 0)
    notes_extracted = stats.get('notes_extracted', 0)
    
    if papers_found == 0:
        console.print("[red]⚠️ No papers found. Try broadening your search terms.[/red]")
    elif notes_extracted == 0:
        console.print("[yellow]⚠️ No notes extracted. This might indicate API quota issues.[/yellow]")
    
    # Top papers
    if 'papers' in results and results['papers']:
        console.print("\n[bold cyan]📚 Top Papers Found:[/bold cyan]")
        for i, paper in enumerate(results['papers'][:5], 1):
            year = paper.published_date.year if hasattr(paper, 'published_date') and paper.published_date else 'N/A'
            console.print(f"{i}. [bold]{paper.title}[/bold] ({year})")
            if hasattr(paper, 'authors') and paper.authors:
                authors_str = ', '.join(paper.authors[:3])
                if len(paper.authors) > 3:
                    authors_str += f" et al."
                console.print(f"   [italic]Authors: {authors_str}[/italic]")
            if hasattr(paper, 'citations'):
                console.print(f"   [dim]Citations: {paper.citations}[/dim]")
    
    # Research themes
    if 'themes' in results and results['themes']:
        console.print("\n[bold cyan]🎯 Key Research Themes:[/bold cyan]")
        for i, theme in enumerate(results['themes'][:5], 1):
            console.print(f"{i}. [bold]{theme.title}[/bold]")
            console.print(f"   {theme.description[:100]}...")
            console.print(f"   [dim]Frequency: {theme.frequency}, Confidence: {theme.confidence:.2f}[/dim]")
    
    # Research gaps
    if 'gaps' in results and results['gaps']:
        console.print("\n[bold cyan]🔍 Research Gaps Identified:[/bold cyan]")
        for i, gap in enumerate(results['gaps'][:5], 1):
            console.print(f"{i}. {gap}")

@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=20, help='Number of results to show')
@click.option('--sort-by', '-s', default='relevance', 
              type=click.Choice(['relevance', 'date', 'citations']),
              help='Sort results by')
def search_papers(query, limit, sort_by):
    """Search papers in the database"""
    try:
        with console.status(f"Searching for '{query}'..."):
            # Fixed: Remove the sort_by parameter that was causing the error
            papers = db.search_papers(query, limit, sort_by)
        
        if not papers:
            console.print(f"[yellow]No papers found for query: '{query}'[/yellow]")
            console.print("[blue]💡 Try different keywords or run a research command to populate the database.[/blue]")
            return
        
        papers_table = Table(title=f"Search Results for '{query}' (sorted by {sort_by})", show_header=True)
        papers_table.add_column("Title", style="cyan", max_width=50)
        papers_table.add_column("Authors", style="green", max_width=30)
        papers_table.add_column("Year", style="yellow", justify="center")
        papers_table.add_column("Citations", style="red", justify="right")
        
        for paper in papers:
            authors_str = ', '.join(paper.authors[:2]) if hasattr(paper, 'authors') and paper.authors else 'N/A'
            if hasattr(paper, 'authors') and len(paper.authors) > 2:
                authors_str += f" +{len(paper.authors)-2}"
            
            year = str(paper.published_date.year) if hasattr(paper, 'published_date') and paper.published_date else 'N/A'
            citations = str(getattr(paper, 'citations', 0))
            
            papers_table.add_row(
                paper.title[:47] + "..." if len(paper.title) > 50 else paper.title,
                authors_str,
                year,
                citations
            )
        
        console.print(papers_table)
        console.print(f"\n[green]Found {len(papers)} papers[/green]")
        
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")
        logger.error(f"Search error: {e}", exc_info=True)

@cli.command()
@click.option('--min-frequency', '-f', default=2, help='Minimum theme frequency')
@click.option('--limit', '-l', default=20, help='Maximum themes to show')
def list_themes(min_frequency, limit):
    """List research themes in the database"""
    try:
        with console.status("Fetching research themes..."):
            # Fixed: Pass parameters correctly to match method signature
            themes = db.get_themes(min_frequency=min_frequency, limit=limit)
        
        if not themes:
            console.print(f"[yellow]No themes found with frequency >= {min_frequency}[/yellow]")
            console.print("[blue]💡 Run some research commands to generate themes.[/blue]")
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
        logger.error(f"List themes error: {e}", exc_info=True)

@cli.command()
@click.option('--backup-path', '-b', help='Backup file path')
def backup_db(backup_path):
    """Backup the research database"""
    try:
        import shutil
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backup_research_db_{timestamp}.db"
        
        # Ensure backup directory exists
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Get database path
        db_path = getattr(db, 'db_path', 'data/research.db')
        
        if not Path(db_path).exists():
            console.print(f"[red]❌ Database file not found: {db_path}[/red]")
            return
        
        with console.status("Creating backup..."):
            shutil.copy2(db_path, backup_path)
        
        # Show backup info
        backup_size = Path(backup_path).stat().st_size
        console.print(f"[green]✅ Database backed up to: {backup_path}[/green]")
        console.print(f"[blue]📁 Backup size: {backup_size / 1024:.1f} KB[/blue]")
        
    except Exception as e:
        console.print(f"[red]Backup error: {e}[/red]")
        logger.error(f"Backup error: {e}", exc_info=True)

@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear all data? This cannot be undone!')
def clear_db():
    """Clear all data from the database (use with caution!)"""
    try:
        with console.status("Clearing database..."):
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
        console.print("[blue]💡 Database is now empty and ready for new research.[/blue]")
        
    except Exception as e:
        console.print(f"[red]Error clearing database: {e}[/red]")
        logger.error(f"Clear database error: {e}", exc_info=True)

@cli.command()
def interactive():
    """Start interactive research session"""
    console.print("[bold green]🚀 Interactive Research Session Started[/bold green]")
    console.print("Type 'help' for available commands or 'exit' to quit.\n")
    
    crew = None
    
    while True:
        try:
            command = Prompt.ask("\n[cyan]research>[/cyan]", default="help")
            
            if command.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]👋 Goodbye![/yellow]")
                break
            
            elif command.lower() == 'help':
                console.print("""
[bold cyan]Available Commands:[/bold cyan]
- [green]research <topic>[/green] - Start research on a topic
- [green]stats[/green] - Show database statistics  
- [green]search <query>[/green] - Search papers in database
- [green]themes[/green] - List research themes
- [green]config[/green] - Show configuration
- [green]clear[/green] - Clear screen
- [green]exit[/green] - Exit interactive mode

[bold cyan]Examples:[/bold cyan]
- research machine learning in healthcare
- search neural networks
- themes
""")
            
            elif command.lower() == 'stats':
                try:
                    stats = db.get_stats()
                    for key, value in stats.items():
                        console.print(f"[cyan]{key.title()}:[/cyan] {value}")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    logger.error(f"Stats error: {e}", exc_info=True)
            
            elif command.lower() == 'config':
                display_config_info()
            
            elif command.lower() == 'clear':
                console.clear()
                display_banner()
                console.print("[green]Interactive session active[/green]")
            
            elif command.lower().startswith('search '):
                query = command[7:].strip()
                if query:
                    try:
                        # Fixed: Call search_papers with correct parameters
                        papers = db.search_papers(query, limit=10, sort_by='relevance')
                        console.print(f"[green]Found {len(papers)} papers for '{query}'[/green]")
                        for i, paper in enumerate(papers[:5], 1):
                            console.print(f"{i}. {paper.title}")
                    except Exception as e:
                        console.print(f"[red]Search error: {e}[/red]")
                        logger.error(f"Search error: {e}", exc_info=True)
                else:
                    console.print("[red]Please provide a search query[/red]")
            
            elif command.lower().startswith('research '):
                topic = command[9:].strip()
                if topic:
                    if not crew:
                        console.print("[cyan]🚀 Initializing research crew...[/cyan]")
                        crew = ResearchCrew()
                    
                    console.print(f"[green]Starting research on: {topic}[/green]")
                    console.print("[yellow]Using default settings (max 20 papers)[/yellow]")
                    
                    try:
                        results = crew.execute_research_workflow(topic, max_papers=20)
                        if results.get('success'):
                            display_research_results(results)
                        else:
                            console.print(f"[red]Research failed: {results.get('error', 'Unknown error')}[/red]")
                    except Exception as e:
                        console.print(f"[red]Research error: {e}[/red]")
                        logger.error(f"Research error: {e}", exc_info=True)
                else:
                    console.print("[red]Please provide a research topic[/red]")
            
            elif command.lower() == 'themes':
                try:
                    # Fixed: Call get_themes with correct parameters
                    themes = db.get_themes(min_frequency=1, limit=10)
                    console.print(f"[green]Found {len(themes)} themes:[/green]")
                    for i, theme in enumerate(themes[:10], 1):
                        console.print(f"{i}. [bold]{theme.title}[/bold] (freq: {theme.frequency})")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    logger.error(f"Themes error: {e}", exc_info=True)
            
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logger.error(f"Interactive session error: {e}", exc_info=True)

if __name__ == '__main__':
    cli()