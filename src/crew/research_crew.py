from crewai import Crew, Task, Process
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from ..agents.literature_survey_agent import LiteratureSurveyAgent
from ..agents.note_taking_agent import NoteTakingAgent
from ..agents.theme_synthesizer_agent import ThemeSynthesizerAgent
from ..agents.draft_writer_agent import DraftWriterAgent
from ..agents.citation_generator_agent import CitationGeneratorAgent
from ..storage.database import db
from ..utils.logging import logger
from ..utils.config import config

class ResearchCrew:
    def __init__(self):
        # Initialize all agents
        self.literature_agent = LiteratureSurveyAgent()
        self.note_agent = NoteTakingAgent()
        self.theme_agent = ThemeSynthesizerAgent()
        self.draft_agent = DraftWriterAgent()
        self.citation_agent = CitationGeneratorAgent()
        
        logger.info("Research crew initialized with all agents")
    
    def create_tasks(self, research_topic: str, specific_aspects: List[str] = None,
                    max_papers: int = 100, paper_type: str = "survey") -> List[Task]:
        """Create tasks for the research workflow"""
        
        tasks = []
        
        # Task 1: Literature Survey
        literature_task = Task(
            description=f"""
            Conduct a comprehensive literature survey on the topic: {research_topic}
            
            Requirements:
            - Search multiple academic databases (arXiv, Semantic Scholar)
            - Find {max_papers} most relevant papers
            - Filter and rank papers by relevance
            - Focus on recent publications (last 5 years preferred)
            - Save all papers to the database
            
            Specific aspects to focus on: {specific_aspects or ['general overview']}
            
            Output: List of relevant papers with metadata
            """,
            agent=self.literature_agent.agent,
            expected_output="A curated list of relevant academic papers"
        )
        tasks.append(literature_task)
        
        # Task 2: Note Taking
        note_taking_task = Task(
            description=f"""
            Extract comprehensive notes from the collected papers on: {research_topic}
            
            Requirements:
            - Process each paper's content (abstract, full text if available)
            - Extract key findings, methodologies, and insights
            - Identify limitations and future work directions
            - Categorize notes by type (finding, methodology, limitation, etc.)
            - Save all notes to the database
            
            Focus on insights relevant to: {research_topic}
            
            Output: Comprehensive research notes organized by paper and type
            """,
            agent=self.note_agent.agent,
            expected_output="Structured research notes extracted from papers",
            dependencies=[literature_task]
        )
        tasks.append(note_taking_task)
        
        # Task 3: Theme Synthesis
        theme_synthesis_task = Task(
            description=f"""
            Synthesize research themes and identify patterns from the extracted notes
            
            Requirements:
            - Cluster similar notes and findings
            - Identify major research themes and trends
            - Synthesize coherent theme descriptions
            - Identify research gaps and opportunities
            - Calculate theme frequencies and confidence scores
            - Save themes to the database
            
            Research topic: {research_topic}
            
            Output: Synthesized research themes with identified gaps
            """,
            agent=self.theme_agent.agent,
            expected_output="Research themes, patterns, and identified gaps",
            dependencies=[note_taking_task]
        )
        tasks.append(theme_synthesis_task)
        
        # Task 4: Citation Generation
        citation_task = Task(
            description=f"""
            Generate properly formatted citations for all collected papers
            
            Requirements:
            - Create citations in APA, MLA, and BibTeX formats
            - Generate unique citation keys
            - Validate citation completeness and format
            - Create a master bibliography
            - Save citations to the database
            
            Papers collected for: {research_topic}
            
            Output: Complete citation database with multiple formats
            """,
            agent=self.citation_agent.agent,
            expected_output="Formatted citations and bibliography",
            dependencies=[literature_task]
        )
        tasks.append(citation_task)
        
        # Task 5: Draft Writing
        draft_writing_task = Task(
            description=f"""
            Generate a comprehensive academic {paper_type} paper draft
            
            Requirements:
            - Create structured outline based on research themes
            - Write abstract, introduction, and conclusion
            - Generate sections for each major theme
            - Include proper academic language and flow
            - Insert citation placeholders
            - Synthesize findings into coherent narrative
            
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
                                 progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """Execute the complete research workflow
        
        Args:
            research_topic: The main research topic
            specific_aspects: Specific aspects to focus on
            max_papers: Maximum number of papers to collect
            paper_type: Type of paper to generate (survey, review, analysis)
            date_from: Optional date filter for papers
            progress_callback: Optional callback function for progress updates
                              Called with (step_number, description)
        """
        
        logger.info(f"Starting research workflow for: {research_topic}")
        start_time = datetime.now()
        
        def update_progress(step: int, description: str):
            """Helper function to update progress"""
            if progress_callback:
                try:
                    progress_callback(step, description)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
        
        try:
            # Step 1: Literature Survey
            logger.info("Step 1: Conducting literature survey...")
            update_progress(1, "Searching academic databases for papers...")
            
            papers = self.literature_agent.conduct_literature_survey(
                research_topic, specific_aspects, max_papers, date_from
            )
            
            if not papers:
                logger.error("No papers found. Aborting workflow.")
                return {
                    'success': False,
                    'error': 'No papers found for the given topic',
                    'research_topic': research_topic,
                    'execution_time': str(datetime.now() - start_time)
                }
            
            update_progress(1, f"Found {len(papers)} relevant papers")
            
            # Step 2: Note Taking
            logger.info("Step 2: Extracting research notes...")
            update_progress(2, "Extracting key insights from papers...")
            
            notes = self.note_agent.process_multiple_papers(papers, research_topic)
            
            update_progress(2, f"Extracted {len(notes)} research notes")
            
            # Step 3: Theme Synthesis
            logger.info("Step 3: Synthesizing research themes...")
            update_progress(3, "Identifying research themes and patterns...")
            
            synthesis_result = self.theme_agent.synthesize_research_landscape(notes)
            themes = synthesis_result['themes']
            gaps = synthesis_result['gaps']
            
            update_progress(3, f"Identified {len(themes)} research themes")
            
            # Step 4: Citation Generation
            logger.info("Step 4: Generating citations...")
            update_progress(4, "Generating formatted citations...")
            
            citations = self.citation_agent.generate_citations_for_papers(papers)
            
            update_progress(4, f"Generated {len(citations)} citations")
            
            # Step 5: Draft Writing
            logger.info("Step 5: Writing paper draft...")
            update_progress(5, "Composing academic paper draft...")
            
            draft = self.draft_agent.compile_full_draft(
                research_topic, themes, papers, notes, gaps
            )
            
            # Insert citations into draft
            logger.info("Step 6: Inserting citations...")
            update_progress(5, "Inserting citations into draft...")
            
            for section_key, section_content in draft['sections'].items():
                if isinstance(section_content, dict) and 'content' in section_content:
                    draft['sections'][section_key]['content'] = \
                        self.citation_agent.insert_inline_citations(
                            section_content['content'], citations
                        )
                elif isinstance(section_content, str):
                    draft['sections'][section_key] = \
                        self.citation_agent.insert_inline_citations(section_content, citations)
            
            # Generate bibliography
            bibliography = self.citation_agent.create_bibliography(citations, 'apa')
            draft['bibliography'] = bibliography
            
            # Calculate execution time
            execution_time = datetime.now() - start_time
            
            # Final progress update
            update_progress(5, "Research workflow completed successfully!")
            
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
                'bibliography': bibliography
            }
            
            logger.info(f"Research workflow completed successfully in {execution_time}")
            return results
            
        except Exception as e:
            logger.error(f"Error in research workflow: {e}")
            update_progress(0, f"Error occurred: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'research_topic': research_topic,
                'execution_time': str(datetime.now() - start_time)
            }
    
    def save_results(self, results: Dict[str, Any], output_dir: str = None) -> str:
        """Save research results to files"""
        from pathlib import Path
        import json
        
        if not output_dir:
            output_dir = config.get('storage.outputs_dir', 'data/outputs')
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_clean = "".join(c for c in results['research_topic'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        project_dir = output_path / f"{topic_clean}_{timestamp}"
        project_dir.mkdir(exist_ok=True)
        
        # Save complete results as JSON
        with open(project_dir / "research_results.json", 'w') as f:
            # Convert objects to dictionaries for JSON serialization
            json_results = {
                'success': results['success'],
                'research_topic': results['research_topic'],
                'execution_time': results['execution_time'],
                'statistics': results['statistics'],
                'gaps': results.get('gaps', [])
            }
            json.dump(json_results, f, indent=2, default=str)
        
        # Save paper draft as markdown
        if 'draft' in results:
            draft_content = self.format_draft_as_markdown(results['draft'])
            with open(project_dir / "paper_draft.md", 'w') as f:
                f.write(draft_content)
        
        # Save bibliography
        if 'bibliography' in results:
            with open(project_dir / "bibliography.txt", 'w') as f:
                f.write(results['bibliography'])
        
        # Save papers list
        if 'papers' in results:
            papers_content = "\n".join([
                f"- {paper.title} ({paper.published_date.year if paper.published_date else 'n.d.'})"
                for paper in results['papers']
            ])
            with open(project_dir / "papers_list.txt", 'w') as f:
                f.write(papers_content)
        
        logger.info(f"Results saved to: {project_dir}")
        return str(project_dir)
    
    def format_draft_as_markdown(self, draft: Dict[str, Any]) -> str:
        """Format draft as markdown document"""
        md_content = f"# {draft['title']}\n\n"
        
        # Abstract
        md_content += "## Abstract\n\n"
        md_content += draft['abstract'] + "\n\n"
        
        # Introduction
        md_content += "## 1. Introduction\n\n"
        md_content += draft['introduction'] + "\n\n"
        
        # Theme sections
        section_num = 2
        for key, section in draft['sections'].items():
            if key.startswith('theme_') and isinstance(section, dict):
                md_content += f"## {section_num}. {section['title']}\n\n"
                md_content += section['content'] + "\n\n"
                section_num += 1
        
        # Discussion
        md_content += f"## {section_num}. Discussion\n\n"
        md_content += draft['discussion'] + "\n\n"
        section_num += 1
        
        # Conclusion
        md_content += f"## {section_num}. Conclusion\n\n"
        md_content += draft['conclusion'] + "\n\n"
        
        # Bibliography
        if 'bibliography' in draft:
            md_content += "## References\n\n"
            md_content += draft['bibliography'] + "\n\n"
        
        return md_content