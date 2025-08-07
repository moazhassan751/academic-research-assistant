from crewai import Agent
from typing import List, Dict, Any, Optional
from ..storage.models import Paper, Citation
from ..storage.database import db
from ..tools.citation_formatter import CitationFormatter
from ..tools.Cross_Ref_tool import CrossRefTool
from ..llm.llm_factory import LLMFactory
from ..utils.logging import logger

class CitationGeneratorAgent:
    def __init__(self):
        self.llm = LLMFactory.create_llm()
        self.citation_formatter = CitationFormatter()
        self.crossref_tool = CrossRefTool()
        
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
                
                # Try to get enhanced citation data from CrossRef if we have a DOI
                enhanced_paper = paper
                if paper.doi:
                    try:
                        crossref_paper = self.crossref_tool.get_paper_by_doi(paper.doi)
                        if crossref_paper:
                            # Merge data, preferring more complete information
                            enhanced_paper = self.merge_paper_data(paper, crossref_paper)
                    except Exception as e:
                        logger.warning(f"Could not enhance citation data from CrossRef: {e}")
                
                # Generate new citation
                citation = self.citation_formatter.create_citation(enhanced_paper)
                
                # Save to database
                if db.save_citation(citation):
                    citations.append(citation)
                    logger.info(f"Generated citation for: {paper.title}")
                
            except Exception as e:
                logger.error(f"Error generating citation for paper {paper.id}: {e}")
                continue
        
        return citations
    
    def merge_paper_data(self, original: Paper, crossref: Paper) -> Paper:
        """Merge paper data, preferring more complete information"""
        # Start with original paper
        merged_data = {
            'id': original.id,
            'title': crossref.title if len(crossref.title) > len(original.title) else original.title,
            'authors': crossref.authors if len(crossref.authors) > len(original.authors) else original.authors,
            'abstract': original.abstract if len(original.abstract) > len(crossref.abstract) else crossref.abstract,
            'url': original.url,  # Keep original URL
            'published_date': crossref.published_date if crossref.published_date else original.published_date,
            'venue': crossref.venue if crossref.venue and not original.venue else original.venue,
            'citations': original.citations,  # Keep original citation count
            'pdf_path': original.pdf_path,
            'full_text': original.full_text,
            'keywords': original.keywords,
            'doi': crossref.doi if crossref.doi else original.doi,
            'arxiv_id': original.arxiv_id,
            'created_at': original.created_at
        }
        
        return Paper(**merged_data)
    
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
    
    def enhance_citation_with_crossref(self, citation: Citation, paper: Paper) -> Citation:
        """Enhance citation using CrossRef data"""
        if not paper.doi:
            return citation
        
        try:
            crossref_paper = self.crossref_tool.get_paper_by_doi(paper.doi)
            if not crossref_paper:
                return citation
            
            # Create enhanced citation
            enhanced_citation = Citation(
                id=citation.id,
                paper_id=citation.paper_id,
                citation_key=citation.citation_key,
                apa_format=self.citation_formatter.format_apa(crossref_paper),
                mla_format=self.citation_formatter.format_mla(crossref_paper),
                bibtex=self.citation_formatter.format_bibtex(crossref_paper, citation.citation_key)
            )
            
            return enhanced_citation
            
        except Exception as e:
            logger.error(f"Error enhancing citation with CrossRef: {e}")
            return citation
    
    def generate_citation_report(self, citations: List[Citation]) -> str:
        """Generate a report about citation quality and completeness"""
        total_citations = len(citations)
        if total_citations == 0:
            return "No citations to analyze."
        
        issues = self.validate_citations(citations)
        
        # Calculate statistics
        total_issues = sum(len(v) for v in issues.values())
        completeness_percentage = ((total_citations - total_issues) / total_citations * 100)
        
        # Count citations by source
        source_counts = {'crossref': 0, 'openalex': 0, 'arxiv': 0, 'other': 0}
        for citation in citations:
            paper_id = citation.paper_id
            if 'crossref' in paper_id:
                source_counts['crossref'] += 1
            elif 'openalex' in paper_id:
                source_counts['openalex'] += 1
            elif 'arxiv' in paper_id:
                source_counts['arxiv'] += 1
            else:
                source_counts['other'] += 1
        
        report = f"""
Citation Quality Report
======================

Total Citations: {total_citations}

Source Distribution:
- CrossRef: {source_counts['crossref']}
- OpenAlex: {source_counts['openalex']}
- ArXiv: {source_counts['arxiv']}
- Other: {source_counts['other']}

Issues Found:
- Missing Authors: {len(issues['missing_authors'])}
- Missing Dates: {len(issues['missing_dates'])}
- Missing Titles: {len(issues['missing_titles'])}
- Format Errors: {len(issues['format_errors'])}

Citation Completeness: {completeness_percentage:.1f}%

Recommendations:
- Verify author information for papers with missing authors
- Check publication dates for papers marked as "n.d."
- Review format errors for consistency
- Consider using DOIs for more reliable citation data
"""
        
        return report.strip()