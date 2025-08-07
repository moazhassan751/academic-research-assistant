import re
from typing import Dict, Any, Optional
from datetime import datetime
from ..storage.models import Paper, Citation
from ..utils.logging import logger

class CitationFormatter:
    def __init__(self):
        self.citation_counter = 1
    
    def generate_citation_key(self, paper: Paper) -> str:
        """Generate a citation key for the paper"""
        try:
            # Use first author's last name + year
            first_author = paper.authors[0] if paper.authors else "Unknown"
            last_name = first_author.split()[-1].lower()
            year = paper.published_date.year if paper.published_date else datetime.now().year
            
            # Clean the last name
            last_name = re.sub(r'[^a-z]', '', last_name)
            
            # Handle potential duplicates by adding counter
            base_key = f"{last_name}{year}"
            return base_key
            
        except Exception as e:
            logger.error(f"Error generating citation key: {e}")
            key = f"paper{self.citation_counter}"
            self.citation_counter += 1
            return key
    
    def format_apa(self, paper: Paper) -> str:
        """Format citation in APA style"""
        try:
            # Authors
            if not paper.authors:
                authors = "Unknown Author"
            elif len(paper.authors) == 1:
                authors = paper.authors[0]
            elif len(paper.authors) <= 7:
                authors = ", ".join(paper.authors[:-1]) + f", & {paper.authors[-1]}"
            else:
                authors = ", ".join(paper.authors[:7]) + ", ... " + paper.authors[-1]
            
            # Year
            year = paper.published_date.year if paper.published_date else "n.d."
            
            # Title
            title = paper.title
            
            # Venue/Source
            if paper.venue:
                source = f"*{paper.venue}*"
            elif paper.arxiv_id:
                source = "*arXiv preprint*"
            elif "openalex" in paper.id:
                source = "*Academic Database*"
            elif "crossref" in paper.id:
                source = "*CrossRef Database*"
            else:
                source = "*Retrieved from web*"
            
            # DOI or URL
            if paper.doi:
                doi_url = f"https://doi.org/{paper.doi}"
                return f"{authors} ({year}). {title}. {source}. {doi_url}"
            else:
                return f"{authors} ({year}). {title}. {source}. {paper.url}"
                
        except Exception as e:
            logger.error(f"Error formatting APA citation: {e}")
            return f"Error formatting citation for: {paper.title}"
    
    def format_mla(self, paper: Paper) -> str:
        """Format citation in MLA style"""
        try:
            # First author (Last, First)
            if paper.authors:
                first_author = paper.authors[0]
                name_parts = first_author.split()
                if len(name_parts) >= 2:
                    first_author_mla = f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"
                else:
                    first_author_mla = first_author
                
                # Additional authors
                if len(paper.authors) > 1:
                    authors = first_author_mla + ", et al."
                else:
                    authors = first_author_mla
            else:
                authors = "Unknown Author"
            
            # Title
            title = f'"{paper.title}"'
            
            # Source
            if paper.venue:
                source = f"*{paper.venue}*"
            elif paper.arxiv_id:
                source = "*arXiv*"
            elif "openalex" in paper.id:
                source = "*OpenAlex*"
            elif "crossref" in paper.id:
                source = "*CrossRef*"
            else:
                source = "*Web*"
            
            # Date
            if paper.published_date:
                date = paper.published_date.strftime("%d %b %Y")
            else:
                date = "n.d."
            
            # URL
            if paper.doi:
                url = f"https://doi.org/{paper.doi}"
            else:
                url = paper.url
            
            return f"{authors}. {title} {source}, {date}, {url}."
            
        except Exception as e:
            logger.error(f"Error formatting MLA citation: {e}")
            return f"Error formatting citation for: {paper.title}"
    
    def format_bibtex(self, paper: Paper, citation_key: str) -> str:
        """Format citation in BibTeX style"""
        try:
            # Entry type
            if paper.venue and any(word in paper.venue.lower() for word in ['journal', 'transactions']):
                entry_type = "article"
            elif paper.venue and any(word in paper.venue.lower() for word in ['conference', 'proceedings']):
                entry_type = "inproceedings"
            elif paper.arxiv_id:
                entry_type = "misc"
            else:
                entry_type = "article"
            
            # Build BibTeX entry
            bibtex = f"@{entry_type}{{{citation_key},\n"
            bibtex += f"  title={{{paper.title}}},\n"
            
            if paper.authors:
                authors_str = " and ".join(paper.authors)
                bibtex += f"  author={{{authors_str}}},\n"
            
            if paper.published_date:
                bibtex += f"  year={{{paper.published_date.year}}},\n"
            
            if paper.venue:
                if entry_type == "article":
                    bibtex += f"  journal={{{paper.venue}}},\n"
                elif entry_type == "inproceedings":
                    bibtex += f"  booktitle={{{paper.venue}}},\n"
            
            if paper.doi:
                bibtex += f"  doi={{{paper.doi}}},\n"
            
            if paper.arxiv_id:
                bibtex += f"  archivePrefix={{arXiv}},\n"
                bibtex += f"  eprint={{{paper.arxiv_id}}},\n"
            
            # Add note about data source
            if "openalex" in paper.id:
                bibtex += f"  note={{Retrieved from OpenAlex}},\n"
            elif "crossref" in paper.id:
                bibtex += f"  note={{Retrieved from CrossRef}},\n"
            
            bibtex += f"  url={{{paper.url}}}\n"
            bibtex += "}"
            
            return bibtex
            
        except Exception as e:
            logger.error(f"Error formatting BibTeX citation: {e}")
            return f"@misc{{error,\n  title={{{paper.title}}}\n}}"
    
    def create_citation(self, paper: Paper) -> Citation:
        """Create a complete citation object"""
        citation_key = self.generate_citation_key(paper)
        
        citation = Citation(
            id=f"cite_{paper.id}",
            paper_id=paper.id,
            citation_key=citation_key,
            apa_format=self.format_apa(paper),
            mla_format=self.format_mla(paper),
            bibtex=self.format_bibtex(paper, citation_key)
        )
        
        self.citation_counter += 1
        return citation