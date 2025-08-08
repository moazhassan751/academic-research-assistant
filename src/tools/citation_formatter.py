import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..storage.models import Paper, Citation
from ..utils.logging import logger

class CitationFormatter:
    def __init__(self):
        self.citation_counter = 1
        self.used_keys = set()  # Track used citation keys to avoid duplicates
    
    def generate_citation_key(self, paper: Paper) -> str:
        """Generate a unique citation key for the paper"""
        try:
            # Use first author's last name + year
            if paper.authors and len(paper.authors) > 0:
                first_author = paper.authors[0]
                # Handle cases where author has institutional affiliation in parentheses
                first_author = re.sub(r'\s*\([^)]*\)$', '', first_author)
                # Handle cases with ORCID
                first_author = re.sub(r'\s*\(ORCID:[^)]*\)$', '', first_author)
                
                # Extract last name (assuming Western name format primarily)
                name_parts = first_author.strip().split()
                if name_parts:
                    last_name = name_parts[-1].lower()
                else:
                    last_name = "unknown"
            else:
                last_name = "unknown"
            
            # Get year
            if paper.published_date:
                year = paper.published_date.year
            else:
                year = datetime.now().year
            
            # Clean the last name - remove non-alphabetic characters
            last_name = re.sub(r'[^a-z]', '', last_name)
            if not last_name:  # If nothing left after cleaning
                last_name = "paper"
            
            # Create base key
            base_key = f"{last_name}{year}"
            
            # Handle duplicates by adding suffixes
            final_key = base_key
            suffix_counter = 1
            while final_key in self.used_keys:
                final_key = f"{base_key}_{chr(96 + suffix_counter)}"  # a, b, c, etc.
                suffix_counter += 1
                if suffix_counter > 26:  # If we run out of letters, use numbers
                    final_key = f"{base_key}_{suffix_counter - 26}"
            
            self.used_keys.add(final_key)
            return final_key
            
        except Exception as e:
            logger.error(f"Error generating citation key: {e}")
            # Fallback key
            key = f"paper{self.citation_counter}"
            while key in self.used_keys:
                self.citation_counter += 1
                key = f"paper{self.citation_counter}"
            
            self.used_keys.add(key)
            self.citation_counter += 1
            return key
    
    def clean_author_name(self, author_name: str) -> str:
        """Clean author name by removing institutional affiliations and ORCID info"""
        if not author_name:
            return "Unknown Author"
        
        # Remove institutional affiliations in parentheses
        cleaned = re.sub(r'\s*\([^)]*\)$', '', author_name)
        
        # Remove ORCID information
        cleaned = re.sub(r'\s*\(ORCID:[^)]*\)$', '', cleaned)
        
        return cleaned.strip() or "Unknown Author"
    
    def format_authors_list(self, authors: List[str], style: str = "apa") -> str:
        """Format authors list according to citation style"""
        if not authors:
            return "Unknown Author"
        
        # Clean author names
        clean_authors = [self.clean_author_name(author) for author in authors]
        clean_authors = [author for author in clean_authors if author != "Unknown Author"]
        
        if not clean_authors:
            return "Unknown Author"
        
        if style.lower() == "apa":
            if len(clean_authors) == 1:
                return clean_authors[0]
            elif len(clean_authors) <= 7:
                if len(clean_authors) == 2:
                    return f"{clean_authors[0]} & {clean_authors[1]}"
                else:
                    return ", ".join(clean_authors[:-1]) + f", & {clean_authors[-1]}"
            else:
                return ", ".join(clean_authors[:7]) + ", et al."
        
        elif style.lower() == "mla":
            if len(clean_authors) == 1:
                # Convert to Last, First format
                name_parts = clean_authors[0].split()
                if len(name_parts) >= 2:
                    return f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"
                else:
                    return clean_authors[0]
            else:
                # First author in Last, First format, others as et al.
                first_author = clean_authors[0]
                name_parts = first_author.split()
                if len(name_parts) >= 2:
                    return f"{name_parts[-1]}, {' '.join(name_parts[:-1])}, et al."
                else:
                    return f"{first_author}, et al."
        
        elif style.lower() == "bibtex":
            return " and ".join(clean_authors)
        
        return ", ".join(clean_authors)
    
    def extract_venue_info(self, paper: Paper) -> tuple:
        """Extract venue information and determine publication type"""
        if not paper.venue:
            # Determine source-based venue info
            if hasattr(paper, 'arxiv_id') and paper.arxiv_id:
                return "arXiv preprint", "preprint"
            elif "openalex" in paper.id:
                return "Academic Database", "article"
            elif "crossref" in paper.id:
                return "CrossRef Database", "article"
            else:
                return "Retrieved from web", "misc"
        
        venue = paper.venue
        venue_lower = venue.lower()
        
        # Determine publication type based on venue name
        if any(word in venue_lower for word in ['journal', 'transactions', 'review', 'letters']):
            pub_type = "journal"
        elif any(word in venue_lower for word in ['conference', 'proceedings', 'workshop', 'symposium']):
            pub_type = "conference"
        elif 'arxiv' in venue_lower:
            pub_type = "preprint"
        else:
            pub_type = "article"
        
        return venue, pub_type
    
    def format_apa(self, paper: Paper) -> str:
        """Format citation in APA style with enhanced data handling"""
        try:
            # Authors
            authors = self.format_authors_list(paper.authors, "apa")
            
            # Year
            if paper.published_date:
                year = paper.published_date.year
            else:
                year = "n.d."
            
            # Title
            title = paper.title.strip()
            if not title.endswith('.'):
                title += "."
            
            # Venue/Source
            venue, pub_type = self.extract_venue_info(paper)
            
            if pub_type == "journal":
                source = f"*{venue}*"
            elif pub_type == "conference":
                source = f"*{venue}*"
            elif pub_type == "preprint":
                source = f"*{venue}*"
            else:
                source = f"*{venue}*"
            
            # Add citation count if significant
            citation_info = ""
            if paper.citations and paper.citations > 10:
                citation_info = f" [Cited by {paper.citations}]"
            
            # DOI or URL
            if paper.doi:
                doi_url = f"https://doi.org/{paper.doi}"
                return f"{authors} ({year}). {title} {source}.{citation_info} {doi_url}"
            else:
                return f"{authors} ({year}). {title} {source}.{citation_info} {paper.url}"
                
        except Exception as e:
            logger.error(f"Error formatting APA citation: {e}")
            return f"Error formatting citation for: {paper.title[:50]}..."
    
    def format_mla(self, paper: Paper) -> str:
        """Format citation in MLA style with enhanced data handling"""
        try:
            # Authors
            authors = self.format_authors_list(paper.authors, "mla")
            
            # Title in quotes
            title = f'"{paper.title.strip()}"'
            
            # Source
            venue, pub_type = self.extract_venue_info(paper)
            source = f"*{venue}*"
            
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
            return f"Error formatting citation for: {paper.title[:50]}..."
    
    def format_bibtex(self, paper: Paper, citation_key: str) -> str:
        """Format citation in BibTeX style with enhanced metadata"""
        try:
            venue, pub_type = self.extract_venue_info(paper)
            
            # Determine BibTeX entry type
            if pub_type == "journal":
                entry_type = "article"
            elif pub_type == "conference":
                entry_type = "inproceedings"
            elif pub_type == "preprint":
                entry_type = "misc"
            else:
                entry_type = "article"
            
            # Build BibTeX entry
            bibtex_lines = [f"@{entry_type}{{{citation_key},"]
            
            # Title
            title_clean = paper.title.replace('{', '\\{').replace('}', '\\}')
            bibtex_lines.append(f"  title={{{title_clean}}},")
            
            # Authors
            if paper.authors:
                authors_str = self.format_authors_list(paper.authors, "bibtex")
                authors_clean = authors_str.replace('{', '\\{').replace('}', '\\}')
                bibtex_lines.append(f"  author={{{authors_clean}}},")
            
            # Year
            if paper.published_date:
                bibtex_lines.append(f"  year={{{paper.published_date.year}}},")
            
            # Venue
            if venue and venue not in ["Academic Database", "CrossRef Database", "Retrieved from web"]:
                venue_clean = venue.replace('{', '\\{').replace('}', '\\}')
                if entry_type == "article":
                    bibtex_lines.append(f"  journal={{{venue_clean}}},")
                elif entry_type == "inproceedings":
                    bibtex_lines.append(f"  booktitle={{{venue_clean}}},")
                else:
                    bibtex_lines.append(f"  howpublished={{{venue_clean}}},")
            
            # DOI
            if paper.doi:
                bibtex_lines.append(f"  doi={{{paper.doi}}},")
            
            # ArXiv ID if available
            if hasattr(paper, 'arxiv_id') and paper.arxiv_id:
                bibtex_lines.append(f"  archivePrefix={{arXiv}},")
                bibtex_lines.append(f"  eprint={{{paper.arxiv_id}}},")
            
            # Citations if significant
            if paper.citations and paper.citations > 0:
                bibtex_lines.append(f"  note={{Cited by {paper.citations} papers}},")
            
            # Source annotation
            if "openalex" in paper.id:
                bibtex_lines.append(f"  note={{Retrieved from OpenAlex database}},")
            elif "crossref" in paper.id:
                bibtex_lines.append(f"  note={{Retrieved from CrossRef database}},")
            
            # URL (always include)
            bibtex_lines.append(f"  url={{{paper.url}}}")
            
            bibtex_lines.append("}")
            
            return "\n".join(bibtex_lines)
            
        except Exception as e:
            logger.error(f"Error formatting BibTeX citation: {e}")
            title_safe = paper.title.replace('{', '\\{').replace('}', '\\}')
            return f"@misc{{error,\n  title={{{title_safe}}},\n  note={{Error in citation formatting}}\n}}"
    
    def format_chicago(self, paper: Paper) -> str:
        """Format citation in Chicago style"""
        try:
            # Authors
            if not paper.authors:
                authors = "Unknown Author"
            else:
                first_author = self.clean_author_name(paper.authors[0])
                if len(paper.authors) == 1:
                    authors = first_author
                elif len(paper.authors) == 2:
                    second_author = self.clean_author_name(paper.authors[1])
                    authors = f"{first_author} and {second_author}"
                else:
                    authors = f"{first_author} et al."
            
            # Title
            title = f'"{paper.title.strip()}"'
            
            # Venue and date
            venue, pub_type = self.extract_venue_info(paper)
            
            if paper.published_date:
                if pub_type == "journal":
                    date_str = paper.published_date.strftime("%B %d, %Y")
                else:
                    date_str = str(paper.published_date.year)
            else:
                date_str = "n.d."
            
            # URL
            if paper.doi:
                url = f"https://doi.org/{paper.doi}"
            else:
                url = paper.url
            
            if pub_type == "journal":
                return f'{authors}. {title} *{venue}*, {date_str}. {url}.'
            else:
                return f'{authors}. {title} {venue}, {date_str}. {url}.'
                
        except Exception as e:
            logger.error(f"Error formatting Chicago citation: {e}")
            return f"Error formatting citation for: {paper.title[:50]}..."
    
    def create_citation(self, paper: Paper) -> Citation:
        """Create a complete citation object with multiple formats"""
        citation_key = self.generate_citation_key(paper)
        
        try:
            citation = Citation(
                id=f"cite_{paper.id}",
                paper_id=paper.id,
                citation_key=citation_key,
                apa_format=self.format_apa(paper),
                mla_format=self.format_mla(paper),
                bibtex=self.format_bibtex(paper, citation_key)
            )
            
            # Add Chicago format if Citation model supports it
            if hasattr(citation, 'chicago_format'):
                citation.chicago_format = self.format_chicago(paper)
            
            return citation
            
        except Exception as e:
            logger.error(f"Error creating citation object: {e}")
            # Return a minimal citation object
            return Citation(
                id=f"cite_{paper.id}",
                paper_id=paper.id,
                citation_key=citation_key,
                apa_format=f"Error formatting citation for: {paper.title[:50]}...",
                mla_format=f"Error formatting citation for: {paper.title[:50]}...",
                bibtex=f"@misc{{{citation_key},\n  title={{{paper.title}}}\n}}"
            )
    
    def create_bibliography(self, papers: List[Paper], style: str = "apa") -> str:
        """Create a formatted bibliography from a list of papers"""
        bibliography_lines = []
        
        # Sort papers by first author's last name
        sorted_papers = sorted(papers, key=lambda p: self._get_sort_key(p))
        
        for paper in sorted_papers:
            try:
                if style.lower() == "apa":
                    citation = self.format_apa(paper)
                elif style.lower() == "mla":
                    citation = self.format_mla(paper)
                elif style.lower() == "chicago":
                    citation = self.format_chicago(paper)
                else:
                    citation = self.format_apa(paper)  # Default to APA
                
                bibliography_lines.append(citation)
                
            except Exception as e:
                logger.error(f"Error adding paper to bibliography: {e}")
                bibliography_lines.append(f"Error formatting: {paper.title[:50]}...")
        
        return "\n\n".join(bibliography_lines)
    
    def _get_sort_key(self, paper: Paper) -> str:
        """Get sorting key for bibliography ordering"""
        try:
            if paper.authors and len(paper.authors) > 0:
                first_author = self.clean_author_name(paper.authors[0])
                # Extract last name for sorting
                name_parts = first_author.split()
                if name_parts:
                    return name_parts[-1].lower()
            
            # Fallback to title
            return paper.title.lower()
            
        except Exception:
            return "zzz"  # Sort problematic entries to the end
    
    def export_bibtex_file(self, papers: List[Paper], filename: str = None) -> str:
        """Export papers as a BibTeX file content"""
        bibtex_entries = []
        
        for paper in papers:
            try:
                citation_key = self.generate_citation_key(paper)
                bibtex_entry = self.format_bibtex(paper, citation_key)
                bibtex_entries.append(bibtex_entry)
            except Exception as e:
                logger.error(f"Error creating BibTeX entry for paper: {e}")
                continue
        
        # Add header comment
        header = f"""% Bibliography generated by Academic Research Assistant
% Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
% Total entries: {len(bibtex_entries)}

"""
        
        content = header + "\n\n".join(bibtex_entries)
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"BibTeX file exported to: {filename}")
            except Exception as e:
                logger.error(f"Error writing BibTeX file: {e}")
        
        return content