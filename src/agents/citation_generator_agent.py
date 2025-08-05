from crewai import Agent
from typing import List, Dict, Any, Optional
from ..storage.models import Paper, Citation
from ..storage.database import db
from ..tools.citation_formatter import CitationFormatter
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger

class CitationGeneratorAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        self.citation_formatter = CitationFormatter()
        
        self.agent = Agent(
            role='Citation and Bibliography Specialist',
            goal='Generate properly formatted citations and bibliographies in multiple styles',
            backstory="""You are a meticulous librarian and citation expert who 
            ensures all academic work is properly cited. You understand the 
            nuances of different citation styles and maintain consistency 
            throughout academic documents.""",
            verbose=True,
            llm=self.llm.generate
        )
    
    def generate_citations_for_papers(self, papers: List[Paper]) -> List[Citation]:
        """Generate citations for a list of papers"""
        citations = []
        
        for paper in papers:
            try:
                # Check if citation already exists
                existing_citation = db.get_citation(paper.id)
                if existing_citation:
                    citations.append(existing_citation)
                    continue
                
                # Generate new citation
                citation = self.citation_formatter.create_citation(paper)
                
                # Save to database
                if db.save_citation(citation):
                    citations.append(citation)
                    logger.info(f"Generated citation for: {paper.title}")
                
            except Exception as e:
                logger.error(f"Error generating citation for paper {paper.id}: {e}")
                continue
        
        return citations
    
    def create_bibliography(self, citations: List[Citation], 
                           style: str = "apa") -> str:
        """Create formatted bibliography"""
        if not citations:
            return ""
        
        bibliography_entries = []
        
        for citation in citations:
            if style.lower() == "apa":
                entry = citation.apa_format
            elif style.lower() == "mla":
                entry = citation.mla_format
            elif style.lower() == "bibtex":
                entry = citation.bibtex
            else:
                entry = citation.apa_format  # Default to APA
            
            bibliography_entries.append(entry)
        
        # Sort entries alphabetically for APA/MLA
        if style.lower() in ["apa", "mla"]:
            bibliography_entries.sort()
        
        return "\n\n".join(bibliography_entries)
    
    def insert_inline_citations(self, text: str, citations: List[Citation]) -> str:
        """Insert inline citations into text where [Citation] placeholders exist"""
        system_prompt = """You are an expert at inserting inline citations into academic text. 
        Replace [Citation] placeholders with appropriate citations in APA format."""
        
        citations_list = "\n".join([f"- {cite.citation_key}: {cite.apa_format}" 
                                   for cite in citations])
        
        prompt = f"""
        Text with [Citation] placeholders:
        {text}
        
        Available Citations:
        {citations_list}
        
        Replace each [Citation] placeholder with the most appropriate citation key 
        in APA format (Author, Year). Consider the context to choose the best citation.
        
        Return the text with proper inline citations.
        """
        
        try:
            cited_text = self.llm.generate(prompt, system_prompt)
            return cited_text.strip()
        except Exception as e:
            logger.error(f"Error inserting inline citations: {e}")
            return text
    
    def validate_citations(self, citations: List[Citation]) -> Dict[str, List[str]]:
        """Validate citation formats and identify issues"""
        issues = {
            'missing_authors': [],
            'missing_dates': [],
            'missing_titles': [],
            'format_errors': []
        }
        
        for citation in citations:
            citation_key = citation.citation_key
            
            # Check APA format
            apa = citation.apa_format
            if not apa or len(apa) < 20:
                issues['format_errors'].append(f"{citation_key}: APA format too short")
            
            if "n.d." in apa:
                issues['missing_dates'].append(f"{citation_key}: Missing publication date")
            
            if "Unknown" in apa:
                issues['missing_authors'].append(f"{citation_key}: Missing author information")
        
        return issues
    
    def generate_citation_report(self, citations: List[Citation]) -> str:
        """Generate a report about citation quality and completeness"""
        total_citations = len(citations)
        issues = self.validate_citations(citations)
        
        report = f"""
Citation Quality Report
======================

Total Citations: {total_citations}

Issues Found:
- Missing Authors: {len(issues['missing_authors'])}
- Missing Dates: {len(issues['missing_dates'])}
- Missing Titles: {len(issues['missing_titles'])}
- Format Errors: {len(issues['format_errors'])}

Citation Completeness: {((total_citations - sum(len(v) for v in issues.values())) / total_citations * 100):.1f}%

Recommendations:
- Verify author information for papers with missing authors
- Check publication dates for papers marked as "n.d."
- Review format errors for consistency
"""
        
        return report.strip()