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
    from src.utils.export_manager import export_manager
    from src.utils.health_monitor import health_monitor
    from src.utils.error_handler import error_handler
    from src.utils.resource_manager import resource_manager
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
        
        # Display API configurations
        openalex_config = config.get_openalex_config()
        crossref_config = config.get_crossref_config()
        
        config_table.add_row("OpenAlex API", "Enabled" if openalex_config else "Disabled")
        config_table.add_row("CrossRef API", "Enabled" if crossref_config else "Disabled")
        config_table.add_row("ArXiv API", "Enabled")
        
        console.print(config_table)
        
        # Display rate limits
        rate_limits = config.get_rate_limits()
        console.print("\n[bold cyan]API Rate Limits:[/bold cyan]")
        console.print(f"  • OpenAlex: {rate_limits.get('openalex', 10)} req/sec")
        console.print(f"  • CrossRef: {rate_limits.get('crossref', 1)} req/sec")
        console.print(f"  • ArXiv: {rate_limits.get('arxiv', 3)}s delay")
        
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
def export_formats():
    """Display available export formats and their status"""
    try:
        from src.crew.research_crew import ResearchCrew
        
        console.print("[cyan]🔧 Checking export format availability...[/cyan]")
        
        crew = ResearchCrew()
        formats = crew.get_supported_export_formats()
        
        format_table = Table(title="Export Format Availability", show_header=True)
        format_table.add_column("Format", style="cyan")
        format_table.add_column("Status", style="green")
        format_table.add_column("Use Case", style="blue")
        format_table.add_column("Dependencies", style="yellow")
        
        format_info = {
            'markdown': ('✅ Available', 'General documentation', 'Built-in'),
            'txt': ('✅ Available', 'Plain text output', 'Built-in'),
            'json': ('✅ Available', 'Data exchange', 'Built-in'),
            'csv': ('✅ Available', 'Bibliography data', 'Built-in'),
            'html': ('✅ Available', 'Web viewing', 'Built-in'),
            'latex': ('✅ Available', 'Academic publishing', 'Built-in'),
            'pdf': ('PDF generation', 'Professional documents', 'reportlab, pdfkit'),
            'docx': ('Word documents', 'MS Office compatibility', 'python-docx')
        }
        
        for fmt, available in formats.items():
            if fmt in format_info:
                status_text, use_case, deps = format_info[fmt]
                if not available and fmt in ['pdf', 'docx']:
                    status = f"❌ Not Available"
                else:
                    status = status_text
                
                format_table.add_row(fmt.upper(), status, use_case, deps)
        
        console.print(format_table)
        
        # Installation instructions for missing dependencies
        unavailable = [fmt for fmt, available in formats.items() if not available]
        if unavailable:
            console.print("\n[yellow]💡 To enable missing formats, install dependencies:[/yellow]")
            console.print("   pip install reportlab python-docx pdfkit")
            console.print("\n[dim]Note: pdfkit also requires wkhtmltopdf to be installed separately[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Error checking export formats: {e}[/red]")
        logger.error(f"Export formats check error: {e}", exc_info=True)

@cli.command()
def test_apis():
    """Test API connections and configurations"""
    try:
        from src.tools.Open_Alex_tool import OpenAlexTool
        from src.tools.Cross_Ref_tool import CrossRefTool
        from src.tools.arxiv_tool import ArxivTool
        
        console.print("[cyan]🔧 Testing API connections...[/cyan]")
        
        # Test OpenAlex with more comprehensive testing
        console.print("\n[bold cyan]Testing OpenAlex API:[/bold cyan]")
        try:
            openalex = OpenAlexTool(mailto="rmoazhassan555@gmail.com")
            
            # Test with multiple queries to ensure robustness
            test_queries = [
                ("machine learning", 2),
                ("artificial intelligence", 2),
                ("deep learning", 1)
            ]
            
            total_papers = 0
            successful_queries = 0
            
            for query, max_results in test_queries:
                console.print(f"   Testing query: '{query}' (max: {max_results})")
                try:
                    test_result = openalex.search_papers(query, max_results=max_results)
                    if test_result and len(test_result) > 0:
                        total_papers += len(test_result)
                        successful_queries += 1
                        console.print(f"   ✅ Found {len(test_result)} papers")
                        
                        # Show sample paper details
                        if test_result:
                            sample_paper = test_result[0]
                            console.print(f"   📄 Sample: {sample_paper.title[:60]}...")
                            console.print(f"   👤 Authors: {', '.join(sample_paper.authors[:2]) if sample_paper.authors else 'N/A'}")
                            console.print(f"   📊 Citations: {getattr(sample_paper, 'citations', 0)}")
                    else:
                        console.print(f"   ⚠️ No papers found for '{query}'")
                except Exception as query_error:
                    console.print(f"   ❌ Query failed: {str(query_error)[:100]}")
            
            if successful_queries > 0:
                console.print(f"[green]✅ OpenAlex API: Connected (Found {total_papers} papers across {successful_queries} queries)[/green]")
                
                # Test additional functionality
                if total_papers > 0:
                    console.print("   Testing additional features...")
                    try:
                        # Test author search
                        author_papers = openalex.search_by_author("Hinton", max_results=1)
                        if author_papers:
                            console.print(f"   ✅ Author search: Found {len(author_papers)} papers")
                        else:
                            console.print("   ⚠️ Author search: No results")
                    except Exception as e:
                        console.print(f"   ⚠️ Author search error: {str(e)[:50]}")
                
            else:
                console.print("[red]❌ OpenAlex API: No successful queries[/red]")
                
        except ImportError:
            console.print("[red]❌ OpenAlex API: Import error - tool module not found[/red]")
        except Exception as e:
            console.print(f"[red]❌ OpenAlex API: Error - {str(e)[:100]}[/red]")
            logger.error(f"OpenAlex test error: {e}", exc_info=True)
        
        # Test CrossRef with enhanced testing
        console.print("\n[bold cyan]Testing CrossRef API:[/bold cyan]")
        try:
            crossref = CrossRefTool()
            test_result = crossref.search_papers("artificial intelligence", max_results=2)
            if test_result and len(test_result) > 0:
                console.print(f"[green]✅ CrossRef API: Connected (Found {len(test_result)} papers)[/green]")
                sample_paper = test_result[0]
                console.print(f"   📄 Sample: {sample_paper.title[:60]}...")
                console.print(f"   👤 Authors: {', '.join(sample_paper.authors[:2]) if sample_paper.authors else 'N/A'}")
            else:
                console.print("[yellow]⚠️ CrossRef API: Connected but no results[/yellow]")
        except ImportError:
            console.print("[red]❌ CrossRef API: Import error - tool module not found[/red]")
        except Exception as e:
            console.print(f"[red]❌ CrossRef API: Error - {str(e)[:100]}[/red]")
            logger.error(f"CrossRef test error: {e}", exc_info=True)
        
        # Test ArXiv with enhanced testing
        console.print("\n[bold cyan]Testing ArXiv API:[/bold cyan]")
        try:
            arxiv = ArxivTool()
            test_result = arxiv.search_papers("neural networks", max_results=2)
            if test_result and len(test_result) > 0:
                console.print(f"[green]✅ ArXiv API: Connected (Found {len(test_result)} papers)[/green]")
                sample_paper = test_result[0]
                console.print(f"   📄 Sample: {sample_paper.title[:60]}...")
                console.print(f"   👤 Authors: {', '.join(sample_paper.authors[:2]) if sample_paper.authors else 'N/A'}")
            else:
                console.print("[yellow]⚠️ ArXiv API: Connected but no results[/yellow]")
        except ImportError:
            console.print("[red]❌ ArXiv API: Import error - tool module not found[/red]")
        except Exception as e:
            console.print(f"[red]❌ ArXiv API: Error - {str(e)[:100]}[/red]")
            logger.error(f"ArXiv test error: {e}", exc_info=True)
        
        # Summary
        console.print("\n[bold cyan]API Test Summary:[/bold cyan]")
        console.print("✅ = Fully working")
        console.print("⚠️ = Connected but limited results")
        console.print("❌ = Error or not working")
        
    except ImportError as e:
        console.print(f"[red]❌ Import Error: {e}[/red]")
        console.print("Make sure all tool modules are properly installed.")
        console.print("\n[yellow]💡 Troubleshooting:[/yellow]")
        console.print("   - Check if all dependencies are installed: pip install -r requirements.txt")
        console.print("   - Verify your Python path includes the project directory")
        console.print("   - Make sure all __init__.py files are present")
    except Exception as e:
        console.print(f"[red]❌ Test Error: {e}[/red]")
        logger.error(f"API test error: {e}", exc_info=True)

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
@click.option('--export-formats', '-f', multiple=True, 
              type=click.Choice(['markdown', 'pdf', 'docx', 'latex', 'html', 'txt', 'csv', 'json']),
              default=['markdown', 'txt'],
              help='Export formats for drafts and bibliographies (can specify multiple)')
def research(topic, aspects, max_papers, paper_type, recent_only, output_dir, save_results, export_formats):
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
        console.print(f"[dim]Estimated time: {max_papers * 2} seconds (based on API rate limits)[/dim]")
        if not Confirm.ask("Continue anyway?"):
            return
    
    if max_papers < 5:
        console.print("[yellow]⚠️ Warning: Very few papers requested, results may be limited[/yellow]")
    
    # Validate export formats
    crew = ResearchCrew()
    available_formats = crew.get_available_export_formats()
    invalid_formats = [fmt for fmt in export_formats if fmt not in available_formats]
    
    if invalid_formats:
        console.print(f"[yellow]⚠️ Warning: Some export formats are not available due to missing dependencies: {', '.join(invalid_formats)}[/yellow]")
        console.print(f"[dim]Available formats: {', '.join(available_formats)}[/dim]")
        export_formats = [fmt for fmt in export_formats if fmt in available_formats]
        
        if not export_formats:
            console.print("[red]❌ Error: No valid export formats specified[/red]")
            return
    
    # Smart resource optimization
    memory_usage = resource_manager.get_memory_usage()
    if memory_usage > 85:
        console.print(f"[yellow]⚠️ High memory usage detected: {memory_usage:.1f}%[/yellow]")
        optimization = resource_manager.optimize_for_large_research(max_papers)
        recommended_papers = optimization['recommended_max_papers']
        
        if recommended_papers < max_papers:
            console.print(f"[yellow]💡 Recommendation: Reduce --max-papers to {recommended_papers} for better performance[/yellow]")
            if not Confirm.ask(f"Continue with {max_papers} papers anyway?"):
                console.print(f"[green]Using recommended limit of {recommended_papers} papers[/green]")
                max_papers = recommended_papers
    
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
        f"[bold]Export Formats:[/bold] {', '.join(export_formats)}\n"
        f"[bold]Output Directory:[/bold] {output_dir or 'Default'}",
        title="Research Parameters",
        border_style="green"
    ))
    
    if not Confirm.ask("Proceed with research?"):
        console.print("[yellow]Research cancelled by user[/yellow]")
        return
    
    try:
        # Initialize research crew
        console.print("[cyan]🚀 Initializing research crew with OpenAlex & CrossRef...[/cyan]")
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
                output_path = crew.save_results(results, output_dir, list(export_formats))
                console.print(f"[green]✅ Results saved to: {output_path}[/green]")
                console.print(f"[blue]📄 Export formats: {', '.join(export_formats)}[/blue]")
                
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
        console.print("   - Verify LLM API keys (Google/OpenAI)")
        console.print("   - Try reducing --max-papers")
        console.print("   - Run 'python main.py test-apis' to check API connections")
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
    
    # Show data source breakdown
    if 'source_breakdown' in results:
        breakdown = results['source_breakdown']
        console.print(f"\n[bold cyan]📚 Data Sources:[/bold cyan]")
        console.print(f"   • OpenAlex: {breakdown.get('openalex', 0)} papers")
        console.print(f"   • CrossRef: {breakdown.get('crossref', 0)} papers") 
        console.print(f"   • ArXiv: {breakdown.get('arxiv', 0)} papers")
    
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
            source = getattr(paper, 'source', 'Unknown')
            console.print(f"{i}. [bold]{paper.title}[/bold] ({year}) [{source}]")
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
            papers = db.search_papers(query, limit, sort_by)
        
        if not papers:
            console.print(f"[yellow]No papers found for query: '{query}'[/yellow]")
            console.print("[blue]💡 Try different keywords or run a research command to populate the database.[/blue]")
            return
        
        papers_table = Table(title=f"Search Results for '{query}' (sorted by {sort_by})", show_header=True)
        papers_table.add_column("Title", style="cyan", max_width=40)
        papers_table.add_column("Authors", style="green", max_width=25)
        papers_table.add_column("Year", style="yellow", justify="center")
        papers_table.add_column("Source", style="magenta", justify="center")
        papers_table.add_column("Citations", style="red", justify="right")
        
        for paper in papers:
            authors_str = ', '.join(paper.authors[:2]) if hasattr(paper, 'authors') and paper.authors else 'N/A'
            if hasattr(paper, 'authors') and len(paper.authors) > 2:
                authors_str += f" +{len(paper.authors)-2}"
            
            year = str(paper.published_date.year) if hasattr(paper, 'published_date') and paper.published_date else 'N/A'
            citations = str(getattr(paper, 'citations', 0))
            source = getattr(paper, 'source', 'Unknown')
            
            papers_table.add_row(
                paper.title[:37] + "..." if len(paper.title) > 40 else paper.title,
                authors_str,
                year,
                source,
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
def health():
    """Check system and project health"""
    try:
        console.print("[cyan]🔍 Running health check...[/cyan]")
        
        with console.status("Checking system health..."):
            # Get health report
            report = health_monitor.generate_health_report()
        
        # Display the report
        console.print(report)
        
        # Check for critical issues
        project_health = health_monitor.check_project_health()
        system_health = health_monitor.get_health_summary()
        
        # Provide recommendations
        if project_health['project_status'] == 'CRITICAL':
            console.print("\n[red]🚨 CRITICAL ISSUES DETECTED[/red]")
            console.print("[yellow]Recommendations:[/yellow]")
            
            if project_health.get('missing_critical_files'):
                console.print("   - Restore missing critical files from repository")
            
            if project_health.get('missing_directories'):
                console.print("   - Create missing directories or run setup")
            
            if not project_health.get('database_exists'):
                console.print("   - Initialize database by running any research command")
        
        elif system_health['status'] == 'WARNING':
            console.print("\n[yellow]⚠️ PERFORMANCE WARNINGS[/yellow]")
            console.print("[blue]Recommendations:[/blue]")
            console.print("   - Monitor system resources during research")
            console.print("   - Consider reducing --max-papers for large queries")
            console.print("   - Close unnecessary applications")
        
        else:
            console.print("\n[green]✅ System is healthy and ready for research![/green]")
        
        # Show error statistics if available
        error_stats = error_handler.get_statistics()
        if error_stats['total_errors'] > 0:
            console.print(f"\n[yellow]📊 Error Statistics:[/yellow]")
            console.print(f"   Total Errors: {error_stats['total_errors']}")
            console.print(f"   Error Types: {', '.join(error_stats['error_types'].keys())}")
            
            if error_stats['time_since_last_error'] < 300:  # Last 5 minutes
                console.print("   [red]Recent errors detected - check logs for details[/red]")
        
        # Show resource recommendations
        resource_rec = resource_manager.get_system_recommendations()
        if resource_rec['suggestions']:
            console.print(f"\n[blue]💡 Resource Optimization Tips:[/blue]")
            for suggestion in resource_rec['suggestions'][:3]:  # Show top 3
                console.print(f"   - {suggestion}")
    
    except Exception as e:
        console.print(f"[red]❌ Health check error: {e}[/red]")
        logger.error(f"Health check error: {e}", exc_info=True)

@cli.command()
@click.argument('result_dir')
@click.option('--export-formats', '-f', multiple=True, 
              type=click.Choice(['markdown', 'pdf', 'docx', 'latex', 'html', 'txt', 'csv', 'json']),
              default=['pdf', 'docx'],
              help='Export formats to generate (can specify multiple)')
def export(result_dir, export_formats):
    """Export existing research results to different formats"""
    import json
    from pathlib import Path
    
    result_path = Path(result_dir)
    
    if not result_path.exists():
        console.print(f"[red]❌ Error: Result directory does not exist: {result_dir}[/red]")
        return
    
    # Check for required files
    json_file = result_path / "research_results.json"
    if not json_file.exists():
        console.print(f"[red]❌ Error: research_results.json not found in {result_dir}[/red]")
        return
    
    try:
        # Load existing results
        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        console.print(f"[cyan]📂 Loading results from: {result_dir}[/cyan]")
        
        # Initialize crew and check formats
        crew = ResearchCrew()
        available_formats = crew.get_available_export_formats()
        invalid_formats = [fmt for fmt in export_formats if fmt not in available_formats]
        
        if invalid_formats:
            console.print(f"[yellow]⚠️ Warning: Some export formats are not available: {', '.join(invalid_formats)}[/yellow]")
            export_formats = [fmt for fmt in export_formats if fmt in available_formats]
        
        if not export_formats:
            console.print("[red]❌ Error: No valid export formats specified[/red]")
            return
        
        console.print(f"[blue]📄 Exporting to formats: {', '.join(export_formats)}[/blue]")
        
        # Try to reconstruct draft from markdown file if not in JSON
        if 'draft' not in results:
            md_file = result_path / "paper_draft.md"
            if md_file.exists():
                with open(md_file, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                # Create a basic draft structure
                results['draft'] = {
                    'title': results.get('research_topic', 'Research Paper Draft'),
                    'content': md_content
                }
        
        # Load bibliography
        bib_file = result_path / "bibliography.txt"
        if bib_file.exists() and 'bibliography' not in results:
            with open(bib_file, 'r', encoding='utf-8') as f:
                results['bibliography'] = f.read()
        
        # Load papers list for CSV export
        papers = []
        if hasattr(db, 'get_papers_by_topic'):
            try:
                papers = db.get_papers_by_topic(results.get('research_topic', ''))
            except:
                pass
        
        # Export in new formats
        success_count = 0
        for format_type in export_formats:
            try:
                if 'draft' in results:
                    draft_path = str(result_path / f"paper_draft_exported")
                    if export_manager.export_draft(results['draft'], draft_path, format_type):
                        success_count += 1
                        console.print(f"   ✅ Draft exported as {format_type.upper()}")
                
                if 'bibliography' in results:
                    bib_path = str(result_path / f"bibliography_exported")
                    if export_manager.export_bibliography(
                        results['bibliography'], papers, bib_path, format_type
                    ):
                        console.print(f"   ✅ Bibliography exported as {format_type.upper()}")
                        
            except Exception as e:
                console.print(f"   ❌ Failed to export {format_type}: {e}")
        
        console.print(f"\n[green]✅ Export completed! Generated {success_count} new format(s)[/green]")
        console.print(f"[blue]📁 Check directory: {result_dir}[/blue]")
        
    except Exception as e:
        console.print(f"[red]❌ Error during export: {e}[/red]")
        logger.error(f"Export error: {e}", exc_info=True)

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
- [green]test-apis[/green] - Test API connections
- [green]formats[/green] - Show available export formats
- [green]clear[/green] - Clear screen
- [green]exit[/green] - Exit interactive mode

[bold cyan]Examples:[/bold cyan]
- research machine learning in healthcare
- search neural networks
- themes
- formats

[bold cyan]Export Features:[/bold cyan]
Use the CLI commands for advanced export options:
- [yellow]python main.py research "topic" --export-formats pdf docx[/yellow]
- [yellow]python main.py export path/to/results --export-formats pdf[/yellow]
""")
            
            elif command.lower() == 'formats':
                try:
                    crew = ResearchCrew()
                    formats = crew.get_supported_export_formats()
                    available = [fmt for fmt, avail in formats.items() if avail]
                    unavailable = [fmt for fmt, avail in formats.items() if not avail]
                    
                    console.print(f"[green]✅ Available formats: {', '.join(available)}[/green]")
                    if unavailable:
                        console.print(f"[red]❌ Unavailable formats: {', '.join(unavailable)}[/red]")
                        console.print("[yellow]💡 Install dependencies: pip install reportlab python-docx pdfkit[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error checking formats: {e}[/red]")
            
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
                        papers = db.search_papers(query, limit=10, sort_by='relevance')
                        console.print(f"[green]Found {len(papers)} papers for '{query}'[/green]")
                        for i, paper in enumerate(papers[:5], 1):
                            source = getattr(paper, 'source', 'Unknown')
                            console.print(f"{i}. {paper.title} [{source}]")
                    except Exception as e:
                        console.print(f"[red]Search error: {e}[/red]")
                        logger.error(f"Search error: {e}", exc_info=True)
                else:
                    console.print("[red]Please provide a search query[/red]")
            
            elif command.lower().startswith('research '):
                topic = command[9:].strip()
                if topic:
                    if not crew:
                        console.print("[cyan]🚀 Initializing research crew with OpenAlex & CrossRef...[/cyan]")
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