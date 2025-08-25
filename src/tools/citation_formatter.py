import re
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from ..storage.models import Paper, Citation
from ..utils.app_logging import logger

class CitationFormatter:
    def __init__(self):
        self.citation_counter = 1
        self.used_keys = set()  # Track used citation keys to avoid duplicates
        
        # Configuration
        self.max_authors_display = {
            'apa': 20,      # APA 7th edition allows up to 20 authors before et al.
            'mla': 1,       # MLA typically shows first author + et al.
            'chicago': 10,  # Chicago allows more flexibility
            'bibtex': 999   # BibTeX can handle many authors
        }
        
        # DOI pattern for validation
        self.doi_pattern = re.compile(r'^10\.\d{4,}/[^\s]+$')
        
        # Special character mappings for safe formatting
        self.special_chars = {
            '&': '\\&',
            '%': '\\%',
            '$': '\\$',
            '#': '\\#',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}'
        }
    
    def _validate_paper(self, paper: Paper) -> bool:
        """Validate paper object has minimum required data"""
        if not paper:
            logger.error("Paper object is None")
            return False
        
        if not hasattr(paper, 'title') or not paper.title:
            logger.warning(f"Paper {getattr(paper, 'id', 'unknown')} missing title")
            return False
        
        if not hasattr(paper, 'authors'):
            logger.warning(f"Paper {paper.id} missing authors attribute")
            return False
            
        return True
    
    def _sanitize_text(self, text: str, format_type: str = 'general') -> str:
        """Sanitize text for different citation formats"""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Format-specific sanitization
        if format_type == 'bibtex':
            # Escape special LaTeX characters
            for char, escaped in self.special_chars.items():
                text = text.replace(char, escaped)
        elif format_type == 'html':
            # HTML escaping
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        return text
    
    def _validate_doi(self, doi: str) -> bool:
        """Validate DOI format"""
        if not doi:
            return False
        return bool(self.doi_pattern.match(doi.strip()))
    
    def generate_citation_key(self, paper: Paper) -> str:
        """Generate a unique citation key for the paper with enhanced validation"""
        try:
            # Validate input
            if not self._validate_paper(paper):
                logger.warning("Invalid paper object, using fallback citation key")
                return self._generate_fallback_key()
            
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
                    # Handle international characters and special cases
                    last_name = re.sub(r'[^a-zA-Z]', '', last_name)
                else:
                    last_name = "unknown"
            else:
                last_name = "unknown"
            
            # Get year with better date handling
            if hasattr(paper, 'published_date') and paper.published_date:
                if hasattr(paper.published_date, 'year'):
                    year = paper.published_date.year
                else:
                    # Handle string dates
                    try:
                        year = int(str(paper.published_date)[:4])
                    except:
                        year = datetime.now().year
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
                if suffix_counter <= 26:
                    final_key = f"{base_key}_{chr(96 + suffix_counter)}"  # a, b, c, etc.
                else:
                    final_key = f"{base_key}_{suffix_counter - 26}"
                suffix_counter += 1
                
                # Prevent infinite loops
                if suffix_counter > 1000:
                    final_key = f"{base_key}_{datetime.now().timestamp()}"
                    break
            
            self.used_keys.add(final_key)
            return final_key
            
        except Exception as e:
            logger.error(f"Error generating citation key: {e}")
            return self._generate_fallback_key()
    
    def _generate_fallback_key(self) -> str:
        """Generate a fallback citation key when normal generation fails"""
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
        """Format citation in BibTeX style with enhanced metadata and validation"""
        try:
            if not self._validate_paper(paper):
                return self._generate_error_bibtex(citation_key, paper.title if hasattr(paper, 'title') else "Unknown")
            
            venue, pub_type = self.extract_venue_info(paper)
            
            # Determine BibTeX entry type with more precision
            if pub_type == "journal":
                entry_type = "article"
            elif pub_type == "conference":
                entry_type = "inproceedings"
            elif pub_type == "preprint":
                entry_type = "misc"
            elif hasattr(paper, 'arxiv_id') and paper.arxiv_id:
                entry_type = "misc"
            else:
                entry_type = "article"
            
            # Build BibTeX entry
            bibtex_lines = [f"@{entry_type}{{{citation_key},"]
            
            # Title (required field)
            title_clean = self._sanitize_text(paper.title, 'bibtex')
            bibtex_lines.append(f"  title={{{title_clean}}},")
            
            # Authors (handle various cases)
            if paper.authors:
                authors_str = self.format_authors_list(paper.authors, "bibtex")
                authors_clean = self._sanitize_text(authors_str, 'bibtex')
                bibtex_lines.append(f"  author={{{authors_clean}}},")
            else:
                bibtex_lines.append(f"  author={{Unknown Author}},")
            
            # Year
            if hasattr(paper, 'published_date') and paper.published_date:
                if hasattr(paper.published_date, 'year'):
                    year = paper.published_date.year
                else:
                    try:
                        year = int(str(paper.published_date)[:4])
                    except:
                        year = datetime.now().year
                bibtex_lines.append(f"  year={{{year}}},")
            else:
                bibtex_lines.append(f"  year={{{datetime.now().year}}},")
            
            # Venue-specific fields
            if venue and venue not in ["Academic Database", "CrossRef Database", "Retrieved from web"]:
                venue_clean = self._sanitize_text(venue, 'bibtex')
                if entry_type == "article":
                    bibtex_lines.append(f"  journal={{{venue_clean}}},")
                elif entry_type == "inproceedings":
                    bibtex_lines.append(f"  booktitle={{{venue_clean}}},")
                else:
                    bibtex_lines.append(f"  howpublished={{{venue_clean}}},")
            
            # Volume, Number, Pages (if available in venue)
            if hasattr(paper, 'volume') and paper.volume:
                bibtex_lines.append(f"  volume={{{paper.volume}}},")
            if hasattr(paper, 'number') and paper.number:
                bibtex_lines.append(f"  number={{{paper.number}}},")
            if hasattr(paper, 'pages') and paper.pages:
                bibtex_lines.append(f"  pages={{{paper.pages}}},")
            
            # DOI with validation
            if hasattr(paper, 'doi') and paper.doi:
                if self._validate_doi(paper.doi):
                    bibtex_lines.append(f"  doi={{{paper.doi}}},")
                else:
                    logger.warning(f"Invalid DOI format: {paper.doi}")
            
            # ArXiv ID if available
            if hasattr(paper, 'arxiv_id') and paper.arxiv_id:
                bibtex_lines.append(f"  archivePrefix={{arXiv}},")
                bibtex_lines.append(f"  eprint={{{paper.arxiv_id}}},")
                # Add arXiv primary class if available
                if hasattr(paper, 'arxiv_category') and paper.arxiv_category:
                    bibtex_lines.append(f"  primaryClass={{{paper.arxiv_category}}},")
            
            # Keywords if available
            if hasattr(paper, 'keywords') and paper.keywords:
                keywords_str = ", ".join(paper.keywords[:10])  # Limit to 10 keywords
                bibtex_lines.append(f"  keywords={{{keywords_str}}},")
            
            # Abstract if available and not too long
            if hasattr(paper, 'abstract') and paper.abstract and len(paper.abstract) < 500:
                abstract_clean = self._sanitize_text(paper.abstract[:300], 'bibtex')
                if abstract_clean:
                    bibtex_lines.append(f"  abstract={{{abstract_clean}...}},")
            
            # Publisher if available
            if hasattr(paper, 'publisher') and paper.publisher:
                publisher_clean = self._sanitize_text(paper.publisher, 'bibtex')
                bibtex_lines.append(f"  publisher={{{publisher_clean}}},")
            
            # Citations if significant
            if hasattr(paper, 'citations') and paper.citations and paper.citations > 0:
                bibtex_lines.append(f"  note={{Cited by {paper.citations} papers}},")
            
            # Source annotation with enhanced detection
            source_note = None
            if hasattr(paper, 'id') and paper.id:
                if "openalex" in paper.id.lower():
                    source_note = "Retrieved from OpenAlex database"
                elif "crossref" in paper.id.lower():
                    source_note = "Retrieved from CrossRef database"
                elif "arxiv" in paper.id.lower():
                    source_note = "Retrieved from arXiv"
                elif "pubmed" in paper.id.lower():
                    source_note = "Retrieved from PubMed database"
            
            if source_note:
                bibtex_lines.append(f"  note={{{source_note}}},")
            
            # Month if available
            if hasattr(paper, 'published_date') and paper.published_date:
                if hasattr(paper.published_date, 'month'):
                    month_names = ["", "jan", "feb", "mar", "apr", "may", "jun",
                                  "jul", "aug", "sep", "oct", "nov", "dec"]
                    if 1 <= paper.published_date.month <= 12:
                        bibtex_lines.append(f"  month={{{month_names[paper.published_date.month]}}},")
            
            # URL (always include as fallback)
            if hasattr(paper, 'url') and paper.url:
                bibtex_lines.append(f"  url={{{paper.url}}}")
            
            bibtex_lines.append("}")
            
            return "\n".join(bibtex_lines)
            
        except Exception as e:
            logger.error(f"Error formatting BibTeX citation: {e}")
            return self._generate_error_bibtex(citation_key, getattr(paper, 'title', 'Unknown Title'))
    
    def _generate_error_bibtex(self, citation_key: str, title: str) -> str:
        """Generate error BibTeX entry when formatting fails"""
        title_safe = self._sanitize_text(title, 'bibtex')
        return f"@misc{{{citation_key},\n  title={{{title_safe}}},\n  note={{Error in citation formatting}}\n}}"
    
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
    
    def validate_citation_quality(self, paper: Paper) -> Dict[str, Any]:
        """Assess the quality and completeness of citation data"""
        quality_score = 100
        issues = []
        recommendations = []
        
        # Check required fields
        if not paper.title or len(paper.title.strip()) < 5:
            quality_score -= 30
            issues.append("Missing or very short title")
            recommendations.append("Ensure paper has a descriptive title")
        
        if not paper.authors or len(paper.authors) == 0:
            quality_score -= 25
            issues.append("No authors specified")
            recommendations.append("Add author information")
        elif any(len(author.strip()) < 3 for author in paper.authors):
            quality_score -= 10
            issues.append("Some author names are very short")
            recommendations.append("Verify author name completeness")
        
        # Check publication date
        if not hasattr(paper, 'published_date') or not paper.published_date:
            quality_score -= 15
            issues.append("Missing publication date")
            recommendations.append("Add publication date for accurate citation")
        elif hasattr(paper, 'published_date') and paper.published_date:
            try:
                if hasattr(paper.published_date, 'year'):
                    year = paper.published_date.year
                else:
                    year = int(str(paper.published_date)[:4])
                current_year = datetime.now().year
                if year > current_year + 1:
                    quality_score -= 10
                    issues.append("Future publication date seems unlikely")
                elif year < 1800:
                    quality_score -= 10
                    issues.append("Very old publication date may be incorrect")
            except:
                quality_score -= 5
                issues.append("Publication date format issue")
        
        # Check venue information
        if not hasattr(paper, 'venue') or not paper.venue:
            quality_score -= 10
            issues.append("Missing venue information")
            recommendations.append("Add journal/conference venue")
        
        # Check DOI
        if hasattr(paper, 'doi') and paper.doi:
            if not self._validate_doi(paper.doi):
                quality_score -= 10
                issues.append("Invalid DOI format")
                recommendations.append("Verify DOI format (should be 10.xxxx/xxxxx)")
        else:
            quality_score -= 5
            issues.append("Missing DOI")
            recommendations.append("Add DOI if available for better citation tracking")
        
        # Check URL
        if not hasattr(paper, 'url') or not paper.url:
            quality_score -= 5
            issues.append("Missing URL")
        elif paper.url and not (paper.url.startswith('http://') or paper.url.startswith('https://')):
            quality_score -= 5
            issues.append("URL format issue")
            recommendations.append("Ensure URL starts with http:// or https://")
        
        # Assess citation count
        citation_quality = "unknown"
        if hasattr(paper, 'citations') and paper.citations is not None:
            if paper.citations > 100:
                citation_quality = "highly_cited"
            elif paper.citations > 10:
                citation_quality = "well_cited"
            elif paper.citations > 0:
                citation_quality = "cited"
            else:
                citation_quality = "not_cited"
        
        # Overall assessment
        if quality_score >= 90:
            overall_quality = "excellent"
        elif quality_score >= 80:
            overall_quality = "good"
        elif quality_score >= 70:
            overall_quality = "acceptable"
        elif quality_score >= 60:
            overall_quality = "poor"
        else:
            overall_quality = "very_poor"
        
        return {
            "quality_score": max(0, quality_score),
            "overall_quality": overall_quality,
            "citation_impact": citation_quality,
            "issues": issues,
            "recommendations": recommendations,
            "completeness": {
                "has_title": bool(paper.title),
                "has_authors": bool(paper.authors),
                "has_date": bool(getattr(paper, 'published_date', None)),
                "has_venue": bool(getattr(paper, 'venue', None)),
                "has_doi": bool(getattr(paper, 'doi', None)),
                "has_url": bool(getattr(paper, 'url', None))
            }
        }
    
    def suggest_citation_improvements(self, papers: List[Paper]) -> Dict[str, Any]:
        """Analyze a collection of papers and suggest improvements"""
        total_papers = len(papers)
        if total_papers == 0:
            return {"error": "No papers provided"}
        
        quality_scores = []
        common_issues = {}
        
        for paper in papers:
            try:
                quality = self.validate_citation_quality(paper)
                quality_scores.append(quality['quality_score'])
                
                for issue in quality['issues']:
                    common_issues[issue] = common_issues.get(issue, 0) + 1
            except Exception as e:
                logger.error(f"Error analyzing paper {getattr(paper, 'id', 'unknown')}: {e}")
                continue
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Find most common issues
        sorted_issues = sorted(common_issues.items(), key=lambda x: x[1], reverse=True)
        top_issues = sorted_issues[:5]
        
        return {
            "total_papers": total_papers,
            "average_quality_score": round(avg_quality, 2),
            "quality_distribution": {
                "excellent": len([s for s in quality_scores if s >= 90]),
                "good": len([s for s in quality_scores if 80 <= s < 90]),
                "acceptable": len([s for s in quality_scores if 70 <= s < 80]),
                "poor": len([s for s in quality_scores if 60 <= s < 70]),
                "very_poor": len([s for s in quality_scores if s < 60])
            },
            "most_common_issues": [{"issue": issue, "count": count, "percentage": round(count/total_papers*100, 1)} 
                                  for issue, count in top_issues],
            "recommendations": self._generate_collection_recommendations(avg_quality, top_issues)
        }
    
    def _generate_collection_recommendations(self, avg_quality: float, top_issues: List[tuple]) -> List[str]:
        """Generate recommendations for improving citation collection quality"""
        recommendations = []
        
        if avg_quality < 70:
            recommendations.append("Consider reviewing and improving citation data quality before publication")
        
        for issue, count in top_issues:
            if "Missing publication date" in issue and count > 2:
                recommendations.append("Prioritize adding publication dates - essential for academic citations")
            elif "No authors specified" in issue and count > 1:
                recommendations.append("Author information is critical - ensure all papers have author data")
            elif "Missing DOI" in issue and count > 3:
                recommendations.append("DOIs improve citation tracking - add when available")
            elif "Missing venue" in issue and count > 2:
                recommendations.append("Venue information helps categorize publications properly")
        
        if len(recommendations) == 0:
            recommendations.append("Citation quality is good - consider minor improvements for completeness")
        
        return recommendations