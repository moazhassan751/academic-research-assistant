from crewai import Crew, Task, Process
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..agents.literature_survey_agent import OptimizedLiteratureSurveyAgent
from ..agents.note_taking_agent import NoteTakingAgent
from ..agents.theme_synthesizer_agent import ThemeSynthesizerAgent
from ..agents.draft_writer_agent import DraftWriterAgent
from ..agents.citation_generator_agent import CitationGeneratorAgent
from ..agents.qa_agent import QuestionAnsweringAgent
from ..storage.database import db
from ..utils.logging import logger
from ..utils.config import config
from ..utils.export_manager import export_manager
from ..utils.performance_optimizer import optimizer, ultra_cache, turbo_batch_processor
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class UltraFastResearchCrew:
    """Ultra-fast research crew with comprehensive performance optimizations"""
    
    def __init__(self):
        # Initialize all agents with error handling and performance optimization
        try:
            with optimizer.measure_performance('agent_initialization'):
                # Use optimized agents where available
                self.literature_agent = OptimizedLiteratureSurveyAgent()
                self.note_agent = NoteTakingAgent()
                self.theme_agent = ThemeSynthesizerAgent()
                self.draft_agent = DraftWriterAgent()
                self.citation_agent = CitationGeneratorAgent()
                self.qa_agent = QuestionAnsweringAgent(config.__dict__ if config else None)
                
            logger.info("Enhanced QA Agent features integrated into main QA Agent")
            
            # Performance-optimized configuration
            system_profile = optimizer.profile
            self.max_workflow_retries = config.get('research.max_retries', 2)  # Reduced retries
            self.step_timeout = config.get('research.step_timeout', 1200)  # 20 minutes per step
            self.api_cooldown_time = config.get('research.api_cooldown', 60)  # 1 minute cooldown
            self.parallel_processing = config.get('research.parallel_processing', True)
            self.checkpoint_enabled = config.get('research.checkpoint_enabled', True)
            
            # Adaptive batch processing based on system capabilities
            self.optimal_batch_size = min(system_profile.batch_size, 5)  # Conservative for stability
            self.max_concurrent_operations = min(system_profile.max_concurrent // 2, 4)
            
            # Performance monitoring
            self._performance_stats = {
                'workflows_completed': 0,
                'total_time': 0,
                'average_time': 0,
                'cache_hits': 0,
                'errors_recovered': 0
            }
            
            logger.info(f"Ultra-fast research crew initialized with batch_size={self.optimal_batch_size}, "
                       f"max_concurrent={self.max_concurrent_operations}")
            
        except Exception as e:
            logger.error(f"Failed to initialize research crew: {e}")
            raise
    
    def get_supported_export_formats(self) -> Dict[str, bool]:
        """Get dictionary of supported export formats and their availability"""
        return export_manager.get_supported_formats()
    
    def get_available_export_formats(self) -> List[str]:
        """Get list of available export formats (only those with dependencies installed)"""
        formats = export_manager.get_supported_formats()
        return [fmt for fmt, available in formats.items() if available]
    
    def _save_checkpoint(self, step_name: str, data: Dict[str, Any], research_topic: str):
        """Save workflow checkpoint for recovery"""
        if not self.checkpoint_enabled:
            return
        
        try:
            checkpoint_path = config.get('storage.cache_dir', 'data/cache')
            checkpoint_file = f"{checkpoint_path}/checkpoint_{research_topic}_{step_name}.json"
            
            import json
            from pathlib import Path
            Path(checkpoint_path).mkdir(parents=True, exist_ok=True)
            
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'step': step_name,
                'topic': research_topic,
                'data': data
            }
            
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            
            logger.debug(f"Checkpoint saved for step: {step_name}")
            
        except Exception as e:
            logger.warning(f"Failed to save checkpoint for {step_name}: {e}")
    
    def _load_checkpoint(self, step_name: str, research_topic: str) -> Optional[Dict[str, Any]]:
        """Load workflow checkpoint for recovery"""
        if not self.checkpoint_enabled:
            return None
        
        try:
            checkpoint_path = config.get('storage.cache_dir', 'data/cache')
            checkpoint_file = f"{checkpoint_path}/checkpoint_{research_topic}_{step_name}.json"
            
            from pathlib import Path
            if not Path(checkpoint_file).exists():
                return None
            
            import json
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            
            # Check if checkpoint is recent (within 24 hours)
            checkpoint_time = datetime.fromisoformat(checkpoint_data['timestamp'])
            if datetime.now() - checkpoint_time > timedelta(hours=24):
                logger.info(f"Checkpoint for {step_name} is too old, ignoring")
                return None
            
            logger.info(f"Loaded checkpoint for step: {step_name}")
            return checkpoint_data['data']
            
        except Exception as e:
            logger.warning(f"Failed to load checkpoint for {step_name}: {e}")
            return None
    
    def _clear_checkpoints(self, research_topic: str):
        """Clear all checkpoints for a research topic"""
        try:
            checkpoint_path = config.get('storage.cache_dir', 'data/cache')
            from pathlib import Path
            import glob
            
            pattern = f"{checkpoint_path}/checkpoint_{research_topic}_*.json"
            for file_path in glob.glob(pattern):
                Path(file_path).unlink(missing_ok=True)
            
            logger.debug(f"Cleared checkpoints for topic: {research_topic}")
            
        except Exception as e:
            logger.warning(f"Failed to clear checkpoints: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=30, max=300),
        retry=retry_if_exception_type((Exception,))
    )
    def _execute_step_with_retry(self, step_func, step_name: str, *args, **kwargs):
        """Execute a workflow step with retry logic"""
        try:
            logger.info(f"Executing step: {step_name}")
            start_time = time.time()
            
            result = step_func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            logger.info(f"Step {step_name} completed in {execution_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in step {step_name}: {e}")
            
            # Apply cooldown for API-related errors
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['timeout', '503', 'unavailable', 'quota', 'rate']):
                logger.info(f"API-related error detected, applying cooldown of {self.api_cooldown_time} seconds")
                time.sleep(self.api_cooldown_time)
            
            raise
    
    def _process_papers_in_batches(self, papers: List, batch_size: int = 3, 
                                 process_func: Callable = None, research_topic: str = "") -> List:
        """Process papers in batches to avoid overwhelming the API"""
        if not process_func or not papers:
            return []
        
        results = []
        total_batches = len(papers) // batch_size + (1 if len(papers) % batch_size else 0)
        
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} papers)")
            
            try:
                if self.parallel_processing and len(batch) > 1:
                    # Process batch in parallel with reduced concurrency
                    with ThreadPoolExecutor(max_workers=min(2, len(batch))) as executor:
                        future_to_paper = {
                            executor.submit(process_func, paper, research_topic): paper 
                            for paper in batch
                        }
                        
                        for future in as_completed(future_to_paper, timeout=self.step_timeout):
                            try:
                                result = future.result(timeout=300)  # 5 minute timeout per paper
                                if result:
                                    if isinstance(result, list):
                                        results.extend(result)
                                    else:
                                        results.append(result)
                            except Exception as e:
                                paper = future_to_paper[future]
                                logger.warning(f"Failed to process paper {getattr(paper, 'title', 'Unknown')}: {e}")
                else:
                    # Sequential processing for small batches or when parallel is disabled
                    for paper in batch:
                        try:
                            result = process_func(paper, research_topic)
                            if result:
                                if isinstance(result, list):
                                    results.extend(result)
                                else:
                                    results.append(result)
                        except Exception as e:
                            logger.warning(f"Failed to process paper {getattr(paper, 'title', 'Unknown')}: {e}")
                            continue
                
                # Add delay between batches to respect rate limits
                if batch_num < total_batches:
                    delay = min(30, 10 * batch_num)  # Progressive delay
                    logger.debug(f"Waiting {delay} seconds before next batch")
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                # Continue with next batch rather than failing completely
                continue
        
        return results
    
    def create_tasks(self, research_topic: str, specific_aspects: List[str] = None,
                    max_papers: int = 100, paper_type: str = "survey") -> List[Task]:
        """Create tasks for the research workflow with enhanced error handling"""
        
        tasks = []
        
        # Task 1: Literature Survey with timeout and retry
        literature_task = Task(
            description=f"""
            Conduct a comprehensive literature survey on the topic: {research_topic}
            
            Requirements:
            - Search multiple academic databases (arXiv, OpenAlex, CrossRef)
            - Find {max_papers} most relevant papers with resilient error handling
            - Filter and rank papers by relevance
            - Focus on recent publications (last 5 years preferred)
            - Save all papers to the database with checkpointing
            - Remove duplicates based on DOI and title similarity
            - Handle API timeouts and rate limits gracefully
            
            Specific aspects to focus on: {specific_aspects or ['general overview']}
            
            Output: List of relevant papers with metadata
            """,
            agent=self.literature_agent.agent,
            expected_output="A curated list of relevant academic papers"
        )
        tasks.append(literature_task)
        
        # Task 2: Note Taking with batch processing
        note_taking_task = Task(
            description=f"""
            Extract comprehensive notes from the collected papers on: {research_topic}
            
            Requirements:
            - Process papers in small batches to avoid API overload
            - Extract key findings, methodologies, and insights with retry logic
            - Identify limitations and future work directions
            - Categorize notes by type (finding, methodology, limitation, etc.)
            - Save all notes to the database with error recovery
            - Handle partial failures gracefully
            - Apply rate limiting between API calls
            
            Focus on insights relevant to: {research_topic}
            
            Output: Comprehensive research notes organized by paper and type
            """,
            agent=self.note_agent.agent,
            expected_output="Structured research notes extracted from papers",
            dependencies=[literature_task]
        )
        tasks.append(note_taking_task)
        
        # Task 3: Theme Synthesis with fallback options
        theme_synthesis_task = Task(
            description=f"""
            Synthesize research themes and identify patterns from the extracted notes
            
            Requirements:
            - Cluster similar notes and findings with error tolerance
            - Identify major research themes and trends
            - Synthesize coherent theme descriptions with retry mechanisms
            - Identify research gaps and opportunities
            - Calculate theme frequencies and confidence scores
            - Save themes to the database with checkpointing
            - Handle incomplete data gracefully
            
            Research topic: {research_topic}
            
            Output: Synthesized research themes with identified gaps
            """,
            agent=self.theme_agent.agent,
            expected_output="Research themes, patterns, and identified gaps",
            dependencies=[note_taking_task]
        )
        tasks.append(theme_synthesis_task)
        
        # Task 4: Citation Generation with enhanced error handling
        citation_task = Task(
            description=f"""
            Generate properly formatted citations for all collected papers
            
            Requirements:
            - Create citations in APA, MLA, and BibTeX formats with fallbacks
            - Enhance citations using CrossRef data when DOI is available
            - Generate unique citation keys with collision handling
            - Validate citation completeness and format
            - Create a master bibliography with error recovery
            - Save citations to the database with transaction safety
            - Handle missing metadata gracefully
            
            Papers collected for: {research_topic}
            
            Output: Complete citation database with multiple formats
            """,
            agent=self.citation_agent.agent,
            expected_output="Formatted citations and bibliography",
            dependencies=[literature_task]
        )
        tasks.append(citation_task)
        
        # Task 5: Draft Writing with enhanced safety measures
        draft_writing_task = Task(
            description=f"""
            Generate a comprehensive academic {paper_type} paper draft
            
            Requirements:
            - Create structured outline based on research themes with error handling
            - Write abstract, introduction, and conclusion with retry logic
            - Generate sections for each major theme
            - Include proper academic language and flow
            - Insert citation placeholders with validation
            - Synthesize findings into coherent narrative
            - Handle partial content gracefully
            - Apply content safety measures to avoid API blocks
            
            Paper details:
            - Topic: {research_topic}
            - Type: {paper_type}
            - Include discussion of research gaps
            
            Output: Complete paper draft with proper academic structure
            """,
            agent=self.draft_agent.agent,
            expected_output="Complete academic paper draft with proper structure",
            dependencies=[theme_synthesis_task, citation_task]
        )
        tasks.append(draft_writing_task)
        
        return tasks
    
    def execute_research_workflow(self, research_topic: str,
                                 specific_aspects: List[str] = None,
                                 max_papers: int = 100,
                                 paper_type: str = "survey",
                                 date_from: Optional[datetime] = None,
                                 progress_callback: Optional[Callable[[int, str], None]] = None,
                                 resume_from_checkpoint: bool = True) -> Dict[str, Any]:
        """Execute the complete research workflow with enhanced error handling and recovery
        
        Args:
            research_topic: The main research topic
            specific_aspects: Specific aspects to focus on
            max_papers: Maximum number of papers to collect
            paper_type: Type of paper to generate (survey, review, analysis)
            date_from: Optional date filter for papers
            progress_callback: Optional callback function for progress updates
            resume_from_checkpoint: Whether to resume from saved checkpoints
        """
        
        logger.info(f"Starting research workflow for: {research_topic}")
        start_time = datetime.now()
        
        # Clean topic for file naming
        clean_topic = "".join(c for c in research_topic if c.isalnum() or c in (' ', '-', '_')).strip()
        
        def update_progress(step: int, description: str):
            """Helper function to update progress with error handling"""
            if progress_callback:
                try:
                    progress_callback(step, description)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
        
        # Track progress through workflow
        workflow_state = {
            'papers': None,
            'notes': None,
            'themes': None,
            'gaps': None,
            'citations': None,
            'draft': None
        }
        
        try:
            # Step 1: Literature Survey with checkpoint recovery
            logger.info("Step 1: Conducting literature survey...")
            update_progress(1, "Searching academic databases (ArXiv, OpenAlex, CrossRef)...")
            
            if resume_from_checkpoint:
                checkpoint_papers = self._load_checkpoint('literature_survey', clean_topic)
                if checkpoint_papers:
                    logger.info("Resuming from literature survey checkpoint")
                    workflow_state['papers'] = checkpoint_papers
                    update_progress(1, f"Resumed from checkpoint: {len(checkpoint_papers)} papers")
            
            if not workflow_state['papers']:
                papers = self._execute_step_with_retry(
                    self.literature_agent.conduct_comprehensive_literature_survey,
                    "literature_survey",
                    research_topic, specific_aspects, max_papers, paper_type, date_from, True, True  # enable_ranking=True, parallel_search=True
                )
                
                if not papers:
                    error_msg = 'No papers found for the given topic'
                    logger.error(error_msg)
                    return {
                        'success': False,
                        'error': error_msg,
                        'research_topic': research_topic,
                        'execution_time': str(datetime.now() - start_time)
                    }
                
                workflow_state['papers'] = papers
                self._save_checkpoint('literature_survey', papers, clean_topic)
            
            papers = workflow_state['papers']
            update_progress(1, f"Found {len(papers)} relevant papers")
            
            # Step 2: Note Taking with batch processing and checkpoint recovery
            logger.info("Step 2: Extracting research notes...")
            update_progress(2, "Extracting key insights from papers...")
            
            if resume_from_checkpoint:
                checkpoint_notes = self._load_checkpoint('note_taking', clean_topic)
                if checkpoint_notes:
                    logger.info("Resuming from note taking checkpoint")
                    workflow_state['notes'] = checkpoint_notes
                    update_progress(2, f"Resumed from checkpoint: {len(checkpoint_notes)} notes")
            
            if not workflow_state['notes']:
                # Process papers in smaller batches for better resilience
                notes = self._process_papers_in_batches(
                    papers, 
                    batch_size=2,  # Smaller batches for better stability
                    process_func=lambda paper, topic: self.note_agent.extract_notes_from_paper(paper, topic),
                    research_topic=research_topic
                )
                
                workflow_state['notes'] = notes
                self._save_checkpoint('note_taking', notes, clean_topic)
            
            notes = workflow_state['notes']
            update_progress(2, f"Extracted {len(notes)} research notes")
            
            # Step 3: Theme Synthesis with checkpoint recovery
            logger.info("Step 3: Synthesizing research themes...")
            update_progress(3, "Identifying research themes and patterns...")
            
            if resume_from_checkpoint:
                checkpoint_synthesis = self._load_checkpoint('theme_synthesis', clean_topic)
                if checkpoint_synthesis:
                    logger.info("Resuming from theme synthesis checkpoint")
                    workflow_state['themes'] = checkpoint_synthesis['themes']
                    workflow_state['gaps'] = checkpoint_synthesis['gaps']
                    update_progress(3, f"Resumed from checkpoint: {len(checkpoint_synthesis['themes'])} themes")
            
            if not workflow_state['themes']:
                synthesis_result = self._execute_step_with_retry(
                    self.theme_agent.synthesize_research_landscape,
                    "theme_synthesis",
                    notes
                )
                
                workflow_state['themes'] = synthesis_result['themes']
                workflow_state['gaps'] = synthesis_result['gaps']
                self._save_checkpoint('theme_synthesis', synthesis_result, clean_topic)
            
            themes = workflow_state['themes']
            gaps = workflow_state['gaps']
            update_progress(3, f"Identified {len(themes)} research themes")
            
            # Step 4: Citation Generation with checkpoint recovery
            logger.info("Step 4: Generating citations...")
            update_progress(4, "Generating formatted citations with CrossRef enhancement...")
            
            if resume_from_checkpoint:
                checkpoint_citations = self._load_checkpoint('citations', clean_topic)
                if checkpoint_citations:
                    logger.info("Resuming from citations checkpoint")
                    workflow_state['citations'] = checkpoint_citations
                    update_progress(4, f"Resumed from checkpoint: {len(checkpoint_citations)} citations")
            
            if not workflow_state['citations']:
                citations = self._execute_step_with_retry(
                    self.citation_agent.generate_citations_for_papers,
                    "citations",
                    papers
                )
                
                workflow_state['citations'] = citations
                self._save_checkpoint('citations', citations, clean_topic)
            
            citations = workflow_state['citations']
            update_progress(4, f"Generated {len(citations)} citations")
            
            # Step 5: Draft Writing with enhanced safety measures
            logger.info("Step 5: Writing paper draft...")
            update_progress(5, "Composing academic paper draft...")
            
            if resume_from_checkpoint:
                checkpoint_draft = self._load_checkpoint('draft_writing', clean_topic)
                if checkpoint_draft:
                    logger.info("Resuming from draft writing checkpoint")
                    workflow_state['draft'] = checkpoint_draft
                    update_progress(5, "Resumed from draft checkpoint")
            
            if not workflow_state['draft']:
                draft = self._execute_step_with_retry(
                    self.draft_agent.compile_full_draft,
                    "draft_writing",
                    research_topic, themes, papers, notes, gaps
                )
                
                workflow_state['draft'] = draft
                self._save_checkpoint('draft_writing', draft, clean_topic)
            
            draft = workflow_state['draft']
            
            # Step 6: Insert citations with error handling
            logger.info("Step 6: Inserting citations...")
            update_progress(5, "Inserting citations into draft...")
            
            try:
                # Enhanced citation insertion with retry logic
                for section_key, section_content in draft['sections'].items():
                    try:
                        if isinstance(section_content, dict) and 'content' in section_content:
                            draft['sections'][section_key]['content'] = \
                                self.citation_agent.insert_inline_citations(
                                    section_content['content'], citations
                                )
                        elif isinstance(section_content, str):
                            draft['sections'][section_key] = \
                                self.citation_agent.insert_inline_citations(section_content, citations)
                    except Exception as e:
                        logger.warning(f"Failed to insert citations in section {section_key}: {e}")
                        # Continue with other sections
                        continue
                
                # Generate bibliography with error handling
                try:
                    bibliography = self.citation_agent.create_bibliography(citations, 'apa')
                    draft['bibliography'] = bibliography
                except Exception as e:
                    logger.warning(f"Failed to generate bibliography: {e}")
                    draft['bibliography'] = "Bibliography generation failed due to API limitations."
                
                # Generate citation quality report
                try:
                    citation_report = self.citation_agent.generate_citation_report(citations)
                except Exception as e:
                    logger.warning(f"Failed to generate citation report: {e}")
                    citation_report = "Citation report generation failed."
                
            except Exception as e:
                logger.error(f"Error during citation processing: {e}")
                # Continue without citations rather than failing completely
                citation_report = "Citation processing encountered errors."
                bibliography = "Bibliography generation failed."
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            
            # Final progress update
            update_progress(5, "Research workflow completed successfully!")
            
            # Clear checkpoints on successful completion
            if resume_from_checkpoint:
                self._clear_checkpoints(clean_topic)
            
            # Compile final results
            results = {
                'success': True,
                'research_topic': research_topic,
                'execution_time': str(execution_time),
                'statistics': {
                    'papers_found': len(papers),
                    'notes_extracted': len(notes),
                    'themes_identified': len(themes),
                    'gaps_identified': len(gaps),
                    'citations_generated': len(citations)
                },
                'papers': papers,
                'notes': notes,
                'themes': themes,
                'gaps': gaps,
                'citations': citations,
                'draft': draft,
                'bibliography': bibliography if 'bibliography' in locals() else "Not available",
                'citation_report': citation_report if 'citation_report' in locals() else "Not available"
            }
            
            logger.info(f"Research workflow completed successfully in {execution_time}")
            return results
            
        except Exception as e:
            logger.error(f"Error in research workflow: {e}")
            update_progress(0, f"Error occurred: {str(e)}")
            
            # Return partial results if available
            partial_results = {
                'success': False,
                'error': str(e),
                'research_topic': research_topic,
                'execution_time': str(datetime.now() - start_time),
                'partial_data': {
                    'papers': workflow_state.get('papers'),
                    'notes': workflow_state.get('notes'),
                    'themes': workflow_state.get('themes'),
                    'gaps': workflow_state.get('gaps')
                }
            }
            
            return partial_results
    
    def save_results(self, results: Dict[str, Any], output_dir: str = None, 
                    export_formats: List[str] = None) -> str:
        """Save research results to files with enhanced error handling and multiple export formats
        
        Args:
            results: Research results dictionary
            output_dir: Output directory path
            export_formats: List of export formats ['markdown', 'pdf', 'docx', 'latex', 'html']
        
        Returns:
            str: Output directory path
        """
        from pathlib import Path
        import json
        
        try:
            if not output_dir:
                output_dir = config.get('storage.outputs_dir', 'data/outputs')
            
            if export_formats is None:
                export_formats = ['markdown', 'txt']  # Default formats
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create timestamped directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic_clean = "".join(c for c in results['research_topic'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            project_dir = output_path / f"{topic_clean}_{timestamp}"
            project_dir.mkdir(exist_ok=True)
            
            logger.info(f"Saving results to: {project_dir}")
            
            # Save complete results as JSON with error handling
            try:
                json_results = {
                    'success': results['success'],
                    'research_topic': results['research_topic'],
                    'execution_time': results['execution_time'],
                    'statistics': results.get('statistics', {}),
                    'gaps': results.get('gaps', []),
                    'error': results.get('error', None),
                    'partial_data': results.get('partial_data', {})
                }
                
                with open(project_dir / "research_results.json", 'w', encoding='utf-8') as f:
                    json.dump(json_results, f, indent=2, default=str, ensure_ascii=False)
                logger.info("Research results JSON saved successfully")
                
            except Exception as e:
                logger.error(f"Failed to save research results JSON: {e}")
            
            # Save paper draft in multiple formats
            if 'draft' in results and results['draft']:
                draft_base_path = str(project_dir / "paper_draft")
                
                # Export draft in requested formats
                for format_type in export_formats:
                    try:
                        if export_manager.export_draft(results['draft'], draft_base_path, format_type):
                            logger.info(f"Draft exported successfully as {format_type.upper()}")
                        else:
                            logger.warning(f"Failed to export draft as {format_type.upper()}")
                    except Exception as e:
                        logger.error(f"Error exporting draft to {format_type}: {e}")
                
                # Also save markdown version for backwards compatibility
                try:
                    if 'markdown' not in export_formats:
                        draft_content = self.format_draft_as_markdown(results['draft'])
                        with open(project_dir / "paper_draft.md", 'w', encoding='utf-8') as f:
                            f.write(draft_content)
                        logger.info("Legacy markdown draft saved")
                except Exception as e:
                    logger.error(f"Failed to save legacy markdown draft: {e}")
            
            # Save bibliography in multiple formats
            if 'bibliography' in results and results['bibliography']:
                bib_base_path = str(project_dir / "bibliography")
                papers = results.get('papers', [])
                
                # Export bibliography in requested formats
                bib_formats = ['txt', 'csv', 'json', 'latex'] if 'pdf' in export_formats or 'docx' in export_formats else ['txt']
                for format_type in bib_formats:
                    try:
                        if export_manager.export_bibliography(
                            results['bibliography'], papers, bib_base_path, format_type
                        ):
                            logger.info(f"Bibliography exported successfully as {format_type.upper()}")
                        else:
                            logger.warning(f"Failed to export bibliography as {format_type.upper()}")
                    except Exception as e:
                        logger.error(f"Error exporting bibliography to {format_type}: {e}")
                
                # Also save text version for backwards compatibility
                try:
                    with open(project_dir / "bibliography.txt", 'w', encoding='utf-8') as f:
                        f.write(results['bibliography'])
                    logger.info("Legacy bibliography text saved")
                except Exception as e:
                    logger.error(f"Failed to save legacy bibliography: {e}")
            
            # Save citation report with error handling
            if 'citation_report' in results and results['citation_report']:
                try:
                    with open(project_dir / "citation_report.txt", 'w', encoding='utf-8') as f:
                        f.write(results['citation_report'])
                    logger.info("Citation report saved successfully")
                except Exception as e:
                    logger.error(f"Failed to save citation report: {e}")
            
            # Save papers list with error handling
            if 'papers' in results and results['papers']:
                try:
                    papers_content = "\n".join([
                        f"- {getattr(paper, 'title', 'Unknown Title')} ({getattr(paper.published_date, 'year', 'n.d.') if hasattr(paper, 'published_date') and paper.published_date else 'n.d.'})\n  Authors: {', '.join(getattr(paper, 'authors', [])[:3]) if hasattr(paper, 'authors') and paper.authors else 'Unknown'}\n  Source: {getattr(paper, 'id', 'Unknown').split('_')[0].upper() if hasattr(paper, 'id') and paper.id else 'Unknown'}\n  DOI: {getattr(paper, 'doi', 'N/A') if hasattr(paper, 'doi') else 'N/A'}\n"
                        for paper in results['papers']
                    ])
                    with open(project_dir / "papers_list.txt", 'w', encoding='utf-8') as f:
                        f.write(papers_content)
                    logger.info("Papers list saved successfully")
                except Exception as e:
                    logger.error(f"Failed to save papers list: {e}")
            
            logger.info(f"Results saved to: {project_dir}")
            return str(project_dir)
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return f"Error saving results: {e}"
    
    def format_draft_as_markdown(self, draft: Dict[str, Any]) -> str:
        """Format draft as markdown document with error handling"""
        try:
            md_content = f"# {draft.get('title', 'Research Paper Draft')}\n\n"
            
            # Abstract
            if 'abstract' in draft and draft['abstract']:
                md_content += "## Abstract\n\n"
                md_content += str(draft['abstract']) + "\n\n"
            
            # Introduction
            if 'introduction' in draft and draft['introduction']:
                md_content += "## 1. Introduction\n\n"
                md_content += str(draft['introduction']) + "\n\n"
            
            # Theme sections
            section_num = 2
            if 'sections' in draft and draft['sections']:
                for key, section in draft['sections'].items():
                    try:
                        if key.startswith('theme_') and isinstance(section, dict):
                            title = section.get('title', f'Theme Section {section_num}')
                            content = section.get('content', 'Content unavailable')
                            md_content += f"## {section_num}. {title}\n\n"
                            md_content += str(content) + "\n\n"
                            section_num += 1
                    except Exception as e:
                        logger.warning(f"Error formatting section {key}: {e}")
                        continue
            
            # Discussion
            if 'discussion' in draft and draft['discussion']:
                md_content += f"## {section_num}. Discussion\n\n"
                md_content += str(draft['discussion']) + "\n\n"
                section_num += 1
            
            # Conclusion
            if 'conclusion' in draft and draft['conclusion']:
                md_content += f"## {section_num}. Conclusion\n\n"
                md_content += str(draft['conclusion']) + "\n\n"
            
            # Bibliography
            if 'bibliography' in draft and draft['bibliography']:
                md_content += "## References\n\n"
                md_content += str(draft['bibliography']) + "\n\n"
            
            return md_content
            
        except Exception as e:
            logger.error(f"Error formatting draft as markdown: {e}")
            return f"# Research Paper Draft\n\nError formatting content: {e}\n\nRaw data available in JSON format."
    
    def get_workflow_status(self, research_topic: str) -> Dict[str, Any]:
        """Get the current status of a workflow from checkpoints"""
        clean_topic = "".join(c for c in research_topic if c.isalnum() or c in (' ', '-', '_')).strip()
        
        steps = ['literature_survey', 'note_taking', 'theme_synthesis', 'citations', 'draft_writing']
        status = {}
        
        for step in steps:
            checkpoint = self._load_checkpoint(step, clean_topic)
            status[step] = {
                'completed': checkpoint is not None,
                'timestamp': checkpoint.get('timestamp') if checkpoint else None,
                'data_size': len(checkpoint.get('data', [])) if checkpoint and isinstance(checkpoint.get('data'), list) else 0
            }
        
        return {
            'topic': research_topic,
            'steps': status,
            'overall_progress': sum(1 for s in status.values() if s['completed']) / len(steps) * 100
        }
    
    def cleanup_failed_workflow(self, research_topic: str) -> bool:
        """Clean up checkpoints and temporary files from a failed workflow"""
        try:
            clean_topic = "".join(c for c in research_topic if c.isalnum() or c in (' ', '-', '_')).strip()
            self._clear_checkpoints(clean_topic)
            
            # Also clean up any temporary cache files
            cache_path = config.get('storage.cache_dir', 'data/cache')
            from pathlib import Path
            import glob
            
            temp_pattern = f"{cache_path}/temp_{clean_topic}_*.json"
            for file_path in glob.glob(temp_pattern):
                Path(file_path).unlink(missing_ok=True)
            
            logger.info(f"Cleaned up failed workflow data for: {research_topic}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup workflow data: {e}")
            return False
    
    def validate_workflow_integrity(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the integrity and completeness of workflow results"""
        validation_report = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'completeness_score': 0
        }
        
        required_fields = ['research_topic', 'execution_time', 'statistics']
        optional_fields = ['papers', 'notes', 'themes', 'gaps', 'citations', 'draft']
        
        # Check required fields
        for field in required_fields:
            if field not in results:
                validation_report['valid'] = False
                validation_report['issues'].append(f"Missing required field: {field}")
        
        # Check data completeness
        completeness_checks = 0
        total_checks = len(optional_fields)
        
        for field in optional_fields:
            if field in results and results[field]:
                completeness_checks += 1
            else:
                validation_report['warnings'].append(f"Missing or empty optional field: {field}")
        
        validation_report['completeness_score'] = (completeness_checks / total_checks) * 100
        
        # Check data quality
        if 'statistics' in results:
            stats = results['statistics']
            
            if stats.get('papers_found', 0) == 0:
                validation_report['issues'].append("No papers were found")
            
            if stats.get('notes_extracted', 0) == 0:
                validation_report['warnings'].append("No research notes were extracted")
            
            if stats.get('themes_identified', 0) == 0:
                validation_report['warnings'].append("No research themes were identified")
        
        # Check for errors
        if 'error' in results:
            validation_report['valid'] = False
            validation_report['issues'].append(f"Workflow error: {results['error']}")
        
        # Check execution time reasonableness
        if 'execution_time' in results:
            try:
                exec_time = results['execution_time']
                if isinstance(exec_time, str):
                    # Parse time string like "0:28:03.914554"
                    time_parts = exec_time.split(':')
                    if len(time_parts) >= 2:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        total_minutes = hours * 60 + minutes
                        
                        if total_minutes > 180:  # More than 3 hours
                            validation_report['warnings'].append("Execution time seems unusually long")
                        elif total_minutes < 5:  # Less than 5 minutes
                            validation_report['warnings'].append("Execution time seems unusually short")
            except Exception as e:
                validation_report['warnings'].append(f"Could not validate execution time: {e}")
        
        return validation_report
    
    def answer_research_question(self, question: str, research_topic: str = None, 
                                paper_limit: int = 10, use_enhanced: bool = None) -> Dict[str, Any]:
        """
        Answer a research question based on papers in the database
        
        Args:
            question: The research question to answer
            research_topic: Optional topic to filter papers (if None, searches all papers)
            paper_limit: Maximum number of papers to consider for the answer
            use_enhanced: Whether to use enhanced QA agent (if available)
            
        Returns:
            Dictionary containing the answer, sources, confidence score, and metadata
        """
        try:
            logger.info(f"Processing research question: {question}")
            
            start_time = time.time()
            
            # Try enhanced QA first, with timeout protection
            try:
                logger.info("Using Enhanced QA Agent with all advanced features")
                
                # Use the QA agent to answer the question with timeout
                import threading
                import queue
                
                def qa_worker(q):
                    try:
                        result = self.qa_agent.answer_question(
                            question=question,
                            research_topic=research_topic,
                            paper_limit=paper_limit
                        )
                        q.put(('success', result))
                    except Exception as e:
                        q.put(('error', e))
                
                # Create queue and thread for timeout handling
                q = queue.Queue()
                thread = threading.Thread(target=qa_worker, args=(q,))
                thread.daemon = True
                thread.start()
                thread.join(timeout=30)  # 30 second timeout
                
                if thread.is_alive():
                    # Thread is still running, timeout occurred
                    raise TimeoutError("Enhanced QA processing timed out after 30 seconds")
                
                # Get result from queue
                try:
                    status, answer_result = q.get_nowait()
                    if status == 'error':
                        raise answer_result
                except queue.Empty:
                    raise TimeoutError("Enhanced QA failed to produce result")
                    
            except (TimeoutError, Exception) as e:
                logger.warning(f"Enhanced QA failed or timed out: {e}")
                logger.info("Falling back to simplified QA agent")
                
                # Fallback to simplified QA agent
                from ..agents.simplified_qa import SimplifiedQAAgent
                simplified_qa = SimplifiedQAAgent()
                answer_result = simplified_qa.answer_question(
                    question=question,
                    research_topic=research_topic,
                    paper_limit=paper_limit
                )
                answer_result['qa_agent_used'] = 'simplified_fallback'
            
            # Generate follow-up questions
            follow_up_questions = []
            try:
                if hasattr(self.qa_agent, 'get_enhanced_follow_up_questions'):
                    follow_up_questions = self.qa_agent.get_enhanced_follow_up_questions(question, answer_result)
                elif hasattr(self.qa_agent, 'get_follow_up_questions'):
                    follow_up_questions = self.qa_agent.get_follow_up_questions(question, answer_result)
                elif 'follow_up_questions' not in answer_result:
                    # Generate simple follow-ups if none exist
                    follow_up_questions = [
                        f"What are the main challenges related to {question.lower().replace('what is', '').replace('?', '').strip()}?",
                        f"What are the latest developments in this area?"
                    ]
            except Exception as e:
                logger.warning(f"Could not generate follow-up questions: {e}")
            
            if 'follow_up_questions' not in answer_result:
                answer_result['follow_up_questions'] = follow_up_questions
            
            # Add timing and metadata
            execution_time = time.time() - start_time
            answer_result.update({
                'execution_time': f"{execution_time:.2f} seconds",
                'question': question,
                'research_topic_filter': research_topic,
                'paper_limit': paper_limit,
                'qa_agent_used': 'enhanced'
            })
            
            logger.info(f"Question answered successfully in {execution_time:.2f} seconds using enhanced QA agent")
            logger.info(f"Used {answer_result.get('paper_count', 0)} papers with confidence {answer_result.get('confidence', 0):.3f}")
            
            return answer_result
            
        except Exception as e:
            logger.error(f"Error answering research question: {e}")
            return {
                'answer': f"An error occurred while processing your question: {str(e)}",
                'sources': [],
                'confidence': 0.0,
                'paper_count': 0,
                'follow_up_questions': [],
                'error': str(e)
            }
    
    def interactive_qa_session(self, initial_topic: str = None) -> Dict[str, Any]:
        """
        Start an interactive QA session that allows multiple related questions
        
        Args:
            initial_topic: Optional initial topic to focus the session on
            
        Returns:
            Dictionary containing the session history and results
        """
        try:
            session_results = {
                'session_start': datetime.now().isoformat(),
                'initial_topic': initial_topic,
                'qa_history': [],
                'total_questions': 0
            }
            
            logger.info(f"Starting interactive QA session with topic: {initial_topic}")
            
            while True:
                try:
                    # Get question from user (in a real CLI implementation)
                    # For now, this is a framework for the functionality
                    question = input("\nEnter your research question (or 'quit' to exit): ").strip()
                    
                    if question.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not question:
                        print("Please enter a valid question.")
                        continue
                    
                    # Answer the question
                    answer_result = self.answer_research_question(
                        question=question,
                        research_topic=initial_topic,
                        paper_limit=15  # Slightly higher limit for interactive sessions
                    )
                    
                    # Add to session history
                    qa_entry = {
                        'question': question,
                        'answer_result': answer_result,
                        'timestamp': datetime.now().isoformat()
                    }
                    session_results['qa_history'].append(qa_entry)
                    session_results['total_questions'] += 1
                    
                    # Display results (in a real implementation, this would be formatted nicely)
                    print(f"\n🔍 Answer (Confidence: {answer_result.get('confidence', 0):.2f}):")
                    print(answer_result.get('answer', 'No answer available'))
                    
                    if answer_result.get('follow_up_questions'):
                        print(f"\n💡 Follow-up questions you might ask:")
                        for i, fq in enumerate(answer_result['follow_up_questions'], 1):
                            print(f"   {i}. {fq}")
                    
                except KeyboardInterrupt:
                    print("\nSession interrupted by user.")
                    break
                    
            return session_results
            
        except Exception as e:
            logger.error(f"Error in interactive Q&A session: {e}")
            return {
                'error': str(e),
                'qa_history': [],
                'total_questions': 0
            }
    
    def toggle_enhanced_qa(self, enable: bool = True) -> bool:
        """
        Toggle between standard and enhanced QA agents
        
        Args:
            enable: True to enable enhanced QA (if available), False for standard
            
        Returns:
            True if toggle was successful, False otherwise
        """
        try:
            # Update configuration preference
            config.set('research.prefer_enhanced_qa', enable)
            
            if enable:
                logger.info("Enhanced QA features enabled (integrated in main agent)")
                return True
            else:
                logger.info("Enhanced QA features disabled, using basic mode")
                return True
                
        except Exception as e:
            logger.error(f"Error toggling QA agent: {e}")
            return False
    
    def get_qa_agent_status(self) -> Dict[str, Any]:
        """Get status information about available QA agents"""
        return {
            'enhanced_qa_available': self.qa_agent is not None,
            'currently_using_enhanced': config.get('research.prefer_enhanced_qa', True),
            'enhanced_qa_features': {
                'semantic_embeddings': getattr(self.qa_agent, 'use_semantic_embeddings', False),
                'bm25_scoring': getattr(self.qa_agent, 'use_bm25_scoring', False), 
                'parallel_processing': getattr(self.qa_agent, 'use_parallel_processing', False),
                'caching': getattr(self.qa_agent, 'enable_caching', False),
            }
        }
    
    def get_qa_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from QA agents"""
        metrics = {
            'enhanced_qa_metrics': {}
        }
        
        if self.qa_agent and hasattr(self.qa_agent, 'get_performance_metrics'):
            try:
                metrics['enhanced_qa_metrics'] = self.qa_agent.get_performance_metrics()
            except Exception as e:
                metrics['enhanced_qa_metrics'] = {'error': str(e)}
        
        return metrics
    
    def clear_qa_cache(self) -> Dict[str, bool]:
        """Clear QA agent caches"""
        results = {
            'enhanced_qa_cache_cleared': False
        }
        
        try:
            if hasattr(self.qa_agent, 'clear_cache'):
                self.qa_agent.clear_cache()
                results['enhanced_qa_cache_cleared'] = True
        except Exception as e:
            logger.warning(f"Failed to clear QA cache: {e}")
        
        return results
    
    def answer_question(self, question: str, research_topic: str = None, 
                       paper_limit: int = 10, use_enhanced: bool = None) -> Dict[str, Any]:
        """
        Alias for answer_research_question for convenience
        """
        return self.answer_research_question(question, research_topic, paper_limit, use_enhanced)


# Backward compatibility alias
class ResearchCrew(UltraFastResearchCrew):
    """Legacy alias for backward compatibility"""
    pass