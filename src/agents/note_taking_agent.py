from crewai import Agent
from typing import List, Dict, Any, Optional
from uuid import uuid4
from ..storage.models import Paper, ResearchNote
from ..storage.database import db
from ..tools.pdf_processor import PDFProcessor
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger

class NoteTakingAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        self.pdf_processor = PDFProcessor()
        
        self.agent = Agent(
            role='Research Note-Taking Specialist',
            goal='Extract key insights, methodologies, and findings from academic papers',
            backstory="""You are a meticulous researcher who excels at reading 
            academic papers and extracting the most important information. You 
            can quickly identify key findings, novel methodologies, limitations, 
            and future research directions.""",
            verbose=True,
            llm=self.llm.generate
        )
    
    def extract_key_sections(self, text: str) -> Dict[str, str]:
        """Extract key sections from paper text"""
        system_prompt = """You are an expert at parsing academic papers. 
        Extract key sections from the paper text."""
        
        prompt = f"""
        Paper Text: {text[:3000]}...  # Limit text length
        
        Extract and summarize these sections if present:
        1. Abstract/Summary
        2. Introduction/Background
        3. Methodology/Methods
        4. Key Findings/Results
        5. Limitations
        6. Future Work/Conclusions
        
        Format as JSON with section names as keys.
        If a section is not found, use "Not available" as the value.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            # Parse JSON response (simplified for now)
            return {
                'abstract': 'Extracted abstract',
                'introduction': 'Extracted introduction',
                'methodology': 'Extracted methodology',
                'findings': 'Extracted findings',
                'limitations': 'Extracted limitations',
                'future_work': 'Extracted future work'
            }
        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
            return {}
    
    def identify_key_insights(self, text: str, research_topic: str) -> List[Dict[str, Any]]:
        """Identify key insights relevant to research topic"""
        system_prompt = """You are an expert at identifying key insights from academic papers. 
        Focus on novel findings, important methodologies, and significant conclusions."""
        
        prompt = f"""
        Research Topic: {research_topic}
        Paper Text: {text[:2000]}...
        
        Identify 3-7 key insights from this paper that are relevant to the research topic.
        For each insight, provide:
        1. The insight/finding
        2. Why it's important
        3. Confidence level (0-1)
        4. Type: key_finding, methodology, limitation, or future_work
        
        Format as a list of insights with these fields.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            # Parse and return insights (simplified)
            return [
                {
                    'content': 'Sample key finding',
                    'importance': 'Why this is important',
                    'confidence': 0.8,
                    'type': 'key_finding'
                }
            ]
        except Exception as e:
            logger.error(f"Error identifying insights: {e}")
            return []
    
    def process_paper_content(self, paper: Paper, research_topic: str) -> List[ResearchNote]:
        """Process paper and extract comprehensive notes"""
        logger.info(f"Processing paper: {paper.title}")
        
        notes = []
        
        # Use abstract if full text not available
        content = paper.full_text or paper.abstract
        if not content:
            logger.warning(f"No content available for paper: {paper.id}")
            return notes
        
        # Extract key sections
        sections = self.extract_key_sections(content)
        
        # Create notes for each section
        for section_name, section_content in sections.items():
            if section_content and section_content != "Not available":
                note = ResearchNote(
                    id=str(uuid4()),
                    paper_id=paper.id,
                    content=section_content,
                    note_type=section_name,
                    confidence=0.7
                )
                notes.append(note)
        
        # Identify key insights
        insights = self.identify_key_insights(content, research_topic)
        
        for insight in insights:
            note = ResearchNote(
                id=str(uuid4()),
                paper_id=paper.id,
                content=insight['content'],
                note_type=insight['type'],
                confidence=insight['confidence']
            )
            notes.append(note)
        
        # Save notes to database
        for note in notes:
            db.save_note(note)
        
        logger.info(f"Extracted {len(notes)} notes from paper: {paper.title}")
        return notes
    
    def process_multiple_papers(self, papers: List[Paper], 
                               research_topic: str) -> List[ResearchNote]:
        """Process multiple papers and extract notes"""
        all_notes = []
        
        for paper in papers:
            try:
                paper_notes = self.process_paper_content(paper, research_topic)
                all_notes.extend(paper_notes)
            except Exception as e:
                logger.error(f"Error processing paper {paper.id}: {e}")
                continue
        
        logger.info(f"Total notes extracted: {len(all_notes)}")
        return all_notes