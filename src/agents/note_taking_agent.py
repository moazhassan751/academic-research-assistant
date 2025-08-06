from crewai import Agent
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime  # Add this import
import json
import re
from src.storage.models import Paper, ResearchNote
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
    
    def extract_key_sections(self, text: str, paper_title: str = "") -> Dict[str, str]:
        """Extract key sections from paper text with better error handling"""
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for section extraction")
            return self._create_minimal_sections(text, paper_title)
        
        # Limit text length to avoid token limits
        max_length = 8000
        truncated_text = text[:max_length]
        if len(text) > max_length:
            truncated_text += "...[truncated]"
            logger.debug(f"Text truncated from {len(text)} to {max_length} characters")
        
        system_prompt = """You are an expert at parsing academic papers. 
        Extract key sections from the paper text. Be concise but comprehensive.
        If a section is not clearly present, provide "Not available" as the value."""
        
        prompt = f"""
        Paper Title: {paper_title}
        Paper Text: {truncated_text}
        
        Extract and summarize these sections if present:
        1. Abstract/Summary - Main purpose and key findings
        2. Introduction/Background - Context and motivation  
        3. Methodology/Methods - Approach and techniques used
        4. Key Findings/Results - Main discoveries and outcomes
        5. Limitations - Study limitations and constraints
        6. Future Work/Conclusions - Future directions and implications
        
        Provide response in this exact format:
        ABSTRACT: [content or "Not available"]
        INTRODUCTION: [content or "Not available"] 
        METHODOLOGY: [content or "Not available"]
        FINDINGS: [content or "Not available"]
        LIMITATIONS: [content or "Not available"]
        FUTURE_WORK: [content or "Not available"]
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            
            if not response or response.strip() == "":
                logger.warning("Empty response from LLM for section extraction")
                return self._create_minimal_sections(text, paper_title)
            
            # Parse structured response
            sections = self._parse_structured_response(response)
            
            # Validate that we got some content
            valid_sections = {k: v for k, v in sections.items() 
                            if v and v.strip() and v.strip().lower() != "not available"}
            
            if not valid_sections:
                logger.warning("No valid sections extracted, creating fallback")
                return self._create_minimal_sections(text, paper_title)
            
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
            return self._create_minimal_sections(text, paper_title)
    
    def _parse_structured_response(self, response: str) -> Dict[str, str]:
        """Parse structured LLM response into sections"""
        sections = {
            'abstract': 'Not available',
            'introduction': 'Not available',
            'methodology': 'Not available',
            'findings': 'Not available',
            'limitations': 'Not available',
            'future_work': 'Not available'
        }
        
        # Define patterns for each section
        patterns = {
            'abstract': r'ABSTRACT:\s*(.+?)(?=\n[A-Z_]+:|$)',
            'introduction': r'INTRODUCTION:\s*(.+?)(?=\n[A-Z_]+:|$)',
            'methodology': r'METHODOLOGY:\s*(.+?)(?=\n[A-Z_]+:|$)',
            'findings': r'FINDINGS:\s*(.+?)(?=\n[A-Z_]+:|$)',
            'limitations': r'LIMITATIONS:\s*(.+?)(?=\n[A-Z_]+:|$)',
            'future_work': r'FUTURE_WORK:\s*(.+?)(?=\n[A-Z_]+:|$)'
        }
        
        for section_key, pattern in patterns.items():
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if content and content.lower() != "not available":
                    sections[section_key] = content[:500]  # Limit length
        
        return sections
    
    def _create_minimal_sections(self, text: str, paper_title: str) -> Dict[str, str]:
        """Create minimal sections when LLM extraction fails"""
        # Try to extract first paragraph as abstract-like content
        paragraphs = text.split('\n\n') if text else []
        first_paragraph = paragraphs[0][:300] if paragraphs else "No content available"
        
        return {
            'abstract': first_paragraph if len(first_paragraph) > 50 else "Limited content available",
            'introduction': f"Research on {paper_title}" if paper_title else "Research content",
            'methodology': "Methodology details not clearly available",
            'findings': "Key findings not clearly identified",
            'limitations': "Limitations not specified",
            'future_work': "Future work directions not specified"
        }
    
    def identify_key_insights(self, text: str, research_topic: str, 
                            paper_title: str = "") -> List[Dict[str, Any]]:
        """Identify key insights relevant to research topic with better error handling"""
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for insight extraction")
            return self._create_fallback_insights(paper_title, research_topic)
        
        # Limit text for processing
        max_length = 6000
        sample_text = text[:max_length]
        if len(text) > max_length:
            sample_text += "...[truncated]"
        
        system_prompt = """You are an expert at identifying key insights from academic papers. 
        Focus on novel findings, important methodologies, and significant conclusions.
        Be specific and provide actionable insights."""
        
        prompt = f"""
        Research Topic: {research_topic}
        Paper Title: {paper_title}
        Paper Text: {sample_text}
        
        Identify 3-5 key insights from this paper that are relevant to the research topic.
        For each insight, provide exactly this format:
        
        INSIGHT_1:
        CONTENT: [The insight/finding]
        IMPORTANCE: [Why it's important]
        TYPE: [key_finding/methodology/limitation/future_work]
        CONFIDENCE: [0.6-0.9]
        
        Continue with INSIGHT_2, INSIGHT_3, etc.
        Focus on quality over quantity.
        """
        
        try:
            response = self.llm.generate(prompt, system_prompt)
            
            if not response or response.strip() == "":
                logger.warning("Empty response from LLM for insight extraction")
                return self._create_fallback_insights(paper_title, research_topic)
            
            insights = self._parse_insights_response(response)
            
            if not insights:
                logger.warning("No insights parsed, creating fallback")
                return self._create_fallback_insights(paper_title, research_topic)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error identifying insights: {e}")
            return self._create_fallback_insights(paper_title, research_topic)
    
    def _parse_insights_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse structured insights response"""
        insights = []
        
        # Find all insight blocks
        insight_pattern = r'INSIGHT_\d+:(.*?)(?=INSIGHT_\d+:|$)'
        insight_matches = re.findall(insight_pattern, response, re.DOTALL)
        
        for match in insight_matches:
            insight_text = match.strip()
            
            # Parse individual fields
            content = self._extract_field_content(insight_text, 'CONTENT')
            importance = self._extract_field_content(insight_text, 'IMPORTANCE')
            insight_type = self._extract_field_content(insight_text, 'TYPE')
            confidence_str = self._extract_field_content(insight_text, 'CONFIDENCE')
            
            # Validate and convert confidence
            try:
                confidence = float(confidence_str) if confidence_str else 0.7
                confidence = max(0.1, min(0.9, confidence))  # Clamp between 0.1 and 0.9
            except (ValueError, TypeError):
                confidence = 0.7
            
            # Validate insight type
            valid_types = ['key_finding', 'methodology', 'limitation', 'future_work']
            if insight_type not in valid_types:
                insight_type = 'key_finding'
            
            if content and len(content.strip()) > 10:  # Minimum content requirement
                insights.append({
                    'content': content[:300],  # Limit length
                    'importance': importance[:200] if importance else 'Relevant to research topic',
                    'type': insight_type,
                    'confidence': confidence
                })
        
        return insights[:7]  # Limit to 7 insights
    
    def _extract_field_content(self, text: str, field: str) -> str:
        """Extract field content from insight text"""
        pattern = f'{field}:\\s*(.+?)(?=\\n[A-Z_]+:|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _create_fallback_insights(self, paper_title: str, research_topic: str) -> List[Dict[str, Any]]:
        """Create fallback insights when LLM processing fails"""
        fallback_insights = [
            {
                'content': f"Research contribution related to {research_topic}",
                'importance': "Contributes to the understanding of the research topic",
                'type': 'key_finding',
                'confidence': 0.6
            }
        ]
        
        if paper_title:
            fallback_insights[0]['content'] = f"Key findings from {paper_title} related to {research_topic}"
        
        return fallback_insights
    
    def process_paper_content(self, paper: Paper, research_topic: str) -> List[ResearchNote]:
        """Process paper and extract comprehensive notes with enhanced error handling"""
        logger.info(f"Processing paper: {paper.title}")
        
        notes = []
        
        # Use abstract if full text not available
        content = paper.full_text or paper.abstract
        if not content:
            logger.warning(f"No content available for paper: {paper.id}")
            return self._create_minimal_notes(paper, research_topic)
        
        try:
            # Extract key sections
            sections = self.extract_key_sections(content, paper.title)
            
            # Create notes for each valid section
            for section_name, section_content in sections.items():
                if section_content and section_content.strip() and section_content.strip().lower() != "not available":
                    note = ResearchNote(
                        id=str(uuid4()),
                        paper_id=paper.id,
                        content=section_content[:500],  # Limit note length
                        note_type=section_name,
                        confidence=0.7,
                        created_at=datetime.now()  # FIXED: Use datetime.now() instead of None
                    )
                    notes.append(note)
            
            # Identify key insights
            insights = self.identify_key_insights(content, research_topic, paper.title)
            
            for insight in insights:
                note = ResearchNote(
                    id=str(uuid4()),
                    paper_id=paper.id,
                    content=insight['content'],
                    note_type=insight['type'],
                    confidence=insight['confidence'],
                    created_at=datetime.now()  # FIXED: Use datetime.now() instead of None
                )
                notes.append(note)
            
            # Save notes to database
            saved_count = 0
            for note in notes:
                try:
                    db.save_note(note)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving note: {e}")
            
            logger.info(f"Extracted {len(notes)} notes ({saved_count} saved) from paper: {paper.title}")
            return notes
            
        except Exception as e:
            logger.error(f"Error processing paper content: {e}")
            # Return minimal notes as fallback
            return self._create_minimal_notes(paper, research_topic)
    
    def _create_minimal_notes(self, paper: Paper, research_topic: str) -> List[ResearchNote]:
        """Create minimal notes when processing fails"""
        notes = []
        
        # Create basic note from available information
        content = paper.abstract or f"Paper on {research_topic}: {paper.title}"
        
        note = ResearchNote(
            id=str(uuid4()),
            paper_id=paper.id,
            content=content[:500],
            note_type='abstract',
            confidence=0.5,
            created_at=datetime.now()  # FIXED: Use datetime.now() instead of None
        )
        
        try:
            db.save_note(note)
            notes.append(note)
        except Exception as e:
            logger.error(f"Error saving minimal note: {e}")
        
        return notes
    
    def process_multiple_papers(self, papers: List[Paper], 
                               research_topic: str) -> List[ResearchNote]:
        """Process multiple papers and extract notes with progress tracking"""
        if not papers:
            logger.warning("No papers provided for processing")
            return []
        
        all_notes = []
        successful_papers = 0
        
        logger.info(f"Processing {len(papers)} papers for note extraction")
        
        for i, paper in enumerate(papers, 1):
            try:
                logger.debug(f"Processing paper {i}/{len(papers)}: {paper.title[:50]}...")
                paper_notes = self.process_paper_content(paper, research_topic)
                all_notes.extend(paper_notes)
                
                if paper_notes:
                    successful_papers += 1
                
                # Log progress every 5 papers
                if i % 5 == 0:
                    logger.info(f"Progress: {i}/{len(papers)} papers processed, {len(all_notes)} notes extracted")
                
            except Exception as e:
                logger.error(f"Error processing paper {paper.id} ({paper.title[:30]}...): {e}")
                continue
        
        logger.info(f"Note extraction completed: {len(all_notes)} notes from {successful_papers}/{len(papers)} papers")
        
        return all_notes