from crewai import Agent
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..storage.models import Paper, ResearchNote, ResearchTheme
from ..storage.database import db
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger

class DraftWriterAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        
        self.agent = Agent(
            role='Academic Writing Specialist',
            goal='Generate well-structured, coherent academic content with proper citations',
            backstory="""You are an experienced academic writer who excels at 
            creating clear, well-structured research papers. You understand 
            academic writing conventions and can synthesize complex information 
            into coherent narratives.""",
            verbose=True,
            llm=self.llm.generate
        )
    
    def create_outline(self, research_topic: str, themes: List[ResearchTheme], 
                      paper_type: str = "survey") -> Dict[str, Any]:
        """Create structured outline for academic paper"""
        system_prompt = """You are an expert at creating academic paper outlines. 
        Create a detailed, well-structured outline that follows academic conventions."""
        
        themes_summary = "\n".join([f"- {theme.title}: {theme.description[:150]}..." 
                                   for theme in themes[:10]])
        
        prompt = f"""
        Research Topic: {research_topic}
        Paper Type: {paper_type}
        
        Key Research Themes:
        {themes_summary}
        
        Create a detailed outline for a {paper_type} paper including:
        1. Title
        2. Abstract structure
        3. Introduction sections
        4. Main body sections (based on themes)
        5. Discussion/Analysis sections
        6. Conclusion sections
        
        Format as a hierarchical outline with section numbers and descriptions.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            
            # Parse outline (simplified structure)
            outline = {
                'title': f"A Survey of {research_topic}",
                'sections': [
                    {'number': '1', 'title': 'Introduction', 'content': ''},
                    {'number': '2', 'title': 'Background', 'content': ''},
                    {'number': '3', 'title': 'Literature Review', 'content': ''},
                    {'number': '4', 'title': 'Discussion', 'content': ''},
                    {'number': '5', 'title': 'Conclusion', 'content': ''}
                ]
            }
            
            return outline
            
        except Exception as e:
            logger.error(f"Error creating outline: {e}")
            return self.get_default_outline(research_topic)
    
    def get_default_outline(self, research_topic: str) -> Dict[str, Any]:
        """Get default outline structure"""
        return {
            'title': f"A Survey of {research_topic}",
            'sections': [
                {'number': '1', 'title': 'Introduction', 'content': ''},
                {'number': '2', 'title': 'Background', 'content': ''},
                {'number': '3', 'title': 'Literature Review', 'content': ''},
                {'number': '4', 'title': 'Discussion', 'content': ''},
                {'number': '5', 'title': 'Conclusion', 'content': ''}
            ]
        }
    
    def write_abstract(self, research_topic: str, themes: List[ResearchTheme],
                      gaps: List[str]) -> str:
        """Write abstract for the paper"""
        system_prompt = """You are an expert at writing academic abstracts. 
        Write a clear, concise abstract that summarizes the research survey."""
        
        themes_brief = ", ".join([theme.title for theme in themes[:5]])
        gaps_brief = "; ".join(gaps[:3])
        
        prompt = f"""
        Research Topic: {research_topic}
        Key Themes: {themes_brief}
        Research Gaps: {gaps_brief}
        
        Write a 150-200 word abstract for a literature survey paper that includes:
        1. Brief introduction to the topic
        2. Survey methodology/scope
        3. Key findings and themes
        4. Research gaps identified
        5. Implications for future research
        
        Use formal academic language and structure.
        """
        
        try:
            abstract = self.llm.generate(prompt, system_prompt)
            return abstract.strip()
        except Exception as e:
            logger.error(f"Error writing abstract: {e}")
            return f"This paper presents a comprehensive survey of {research_topic}..."
    
    def write_introduction(self, research_topic: str, papers: List[Paper]) -> str:
        """Write introduction section"""
        system_prompt = """You are an expert at writing academic introductions. 
        Write a compelling introduction that motivates the research topic."""
        
        prompt = f"""
        Research Topic: {research_topic}
        Number of Papers Surveyed: {len(papers)}
        
        Write a 300-400 word introduction that:
        1. Establishes the importance of the topic
        2. Provides context and motivation
        3. Outlines the scope of the survey
        4. Describes the paper's contribution
        5. Provides a roadmap of the paper
        
        Use formal academic language with proper flow and transitions.
        """
        
        try:
            introduction = self.llm.generate(prompt, system_prompt)
            return introduction.strip()
        except Exception as e:
            logger.error(f"Error writing introduction: {e}")
            return f"The field of {research_topic} has gained significant attention..."
    
    def write_theme_section(self, theme: ResearchTheme, 
                           related_papers: List[Paper],
                           related_notes: List[ResearchNote]) -> str:
        """Write a section about a specific research theme"""
        system_prompt = """You are an expert at writing literature review sections. 
        Write a comprehensive section about the research theme with proper citations."""
        
        papers_info = "\n".join([f"- {paper.title} by {', '.join(paper.authors[:2])}..." 
                                for paper in related_papers[:5]])
        
        key_notes = "\n".join([f"- {note.content[:100]}..." 
                              for note in related_notes[:5]])
        
        prompt = f"""
        Theme: {theme.title}
        Description: {theme.description}
        
        Related Papers:
        {papers_info}
        
        Key Findings:
        {key_notes}
        
        Write a 400-500 word section that:
        1. Introduces the theme clearly
        2. Discusses key contributions from the literature
        3. Synthesizes findings across papers
        4. Identifies patterns and trends
        5. Notes any conflicting findings
        
        Use academic language and indicate where citations would be placed with [Citation].
        """
        
        try:
            section = self.llm.generate(prompt, system_prompt)
            return section.strip()
        except Exception as e:
            logger.error(f"Error writing theme section: {e}")
            return f"This section discusses {theme.title}..."
    
    def write_discussion(self, themes: List[ResearchTheme], gaps: List[str]) -> str:
        """Write discussion section"""
        system_prompt = """You are an expert at writing academic discussions. 
        Write a thoughtful discussion that synthesizes findings and implications."""
        
        themes_summary = "\n".join([f"- {theme.title}: {theme.description[:100]}..." 
                                   for theme in themes])
        gaps_list = "\n".join([f"- {gap}" for gap in gaps])
        
        prompt = f"""
        Research Themes Identified:
        {themes_summary}
        
        Research Gaps:
        {gaps_list}
        
        Write a 500-600 word discussion section that:
        1. Synthesizes the main findings across themes
        2. Discusses implications for the field
        3. Addresses research gaps and opportunities
        4. Considers methodological insights
        5. Suggests future research directions
        
        Use academic language with clear argumentation.
        """
        
        try:
            discussion = self.llm.generate(prompt, system_prompt)
            return discussion.strip()
        except Exception as e:
            logger.error(f"Error writing discussion: {e}")
            return "The findings from this survey reveal several important insights..."
    
    def write_conclusion(self, research_topic: str, themes: List[ResearchTheme],
                        gaps: List[str]) -> str:
        """Write conclusion section"""
        system_prompt = """You are an expert at writing academic conclusions. 
        Write a strong conclusion that summarizes contributions and future directions."""
        
        prompt = f"""
        Research Topic: {research_topic}
        Number of Themes: {len(themes)}
        Number of Gaps Identified: {len(gaps)}
        
        Write a 200-300 word conclusion that:
        1. Summarizes the main contributions of the survey
        2. Highlights key insights gained
        3. Emphasizes the most important research gaps
        4. Provides clear future research directions
        5. Concludes with the significance of the work
        
        Use decisive language that reinforces the paper's value.
        """
        
        try:
            conclusion = self.llm.generate(prompt, system_prompt)
            return conclusion.strip()
        except Exception as e:
            logger.error(f"Error writing conclusion: {e}")
            return f"This survey of {research_topic} provides valuable insights..."
    
    def compile_full_draft(self, research_topic: str, themes: List[ResearchTheme],
                          papers: List[Paper], notes: List[ResearchNote],
                          gaps: List[str]) -> Dict[str, str]:
        """Compile complete paper draft"""
        logger.info(f"Compiling full draft for: {research_topic}")
        
        # Create outline
        outline = self.create_outline(research_topic, themes)
        
        # Write each section
        sections = {}
        
        # Abstract
        sections['abstract'] = self.write_abstract(research_topic, themes, gaps)
        
        # Introduction
        sections['introduction'] = self.write_introduction(research_topic, papers)
        
        # Background/Literature Review sections for each theme
        for i, theme in enumerate(themes[:5]):  # Limit to top 5 themes
            theme_papers = [p for p in papers if p.id in theme.papers]
            theme_notes = [n for n in notes if n.paper_id in theme.papers]
            
            section_content = self.write_theme_section(theme, theme_papers, theme_notes)
            sections[f'theme_{i+1}'] = {
                'title': theme.title,
                'content': section_content
            }
        
        # Discussion
        sections['discussion'] = self.write_discussion(themes, gaps)
        
        # Conclusion
        sections['conclusion'] = self.write_conclusion(research_topic, themes, gaps)
        
        # Compile final draft
        draft = {
            'title': outline['title'],
            'abstract': sections['abstract'],
            'introduction': sections['introduction'],
            'sections': sections,
            'discussion': sections['discussion'],
            'conclusion': sections['conclusion'],
            'metadata': {
                'topic': research_topic,
                'themes_count': len(themes),
                'papers_count': len(papers),
                'gaps_count': len(gaps),
                'generated_at': datetime.now().isoformat()
            }
        }
        
        logger.info("Full draft compilation completed")
        return draft