import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote_plus
from ..storage.models import Paper
from ..utils.logging import logger
from ..utils.config import config

class CrossRefTool:
    def __init__(self):
        self.base_url = "https://api.crossref.org/works"
        self.rate_limit_delay = 1.0  # Be polite to CrossRef
        self.last_request_time = 0
        self.session = requests.Session()
        
        # Set user agent with mailto for politeness policy
        mailto = config.get('apis.crossref.mailto', 'rmoazhassan555@gmail.com')
        self.session.headers.update({
            'User-Agent': f'AcademicResearchAssistant/1.0 (mailto:{mailto})'
        })
        
        logger.info("CrossRef tool initialized")
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to the API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_papers(self, query: str, max_results: int = 50, 
                     date_from: Optional[datetime] = None) -> List[Paper]:
        """Search papers using CrossRef API"""
        papers = []
        
        try:
            params = {
                'query': query,
                'rows': min(max_results, 1000),  # CrossRef max is 1000
                'sort': 'score',
                'order': 'desc'
            }
            
            # Add date filter if specified
            if date_from:
                year = date_from.year
                params['filter'] = f'from-pub-date:{year}'
            
            logger.info(f"Searching CrossRef for: {query} (max: {max_results})")
            
            # Make request with rate limiting
            self._rate_limit()
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'message' not in data or 'items' not in data['message']:
                logger.warning("No items found in CrossRef response")
                return papers
            
            # Process results
            items = data['message']['items']
            for item in items[:max_results]:
                paper = self._parse_paper(item)
                if paper:
                    papers.append(paper)
            
            logger.info(f"Retrieved {len(papers)} papers from CrossRef")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CrossRef API request failed: {e}")
        except Exception as e:
            logger.error(f"Error parsing CrossRef response: {e}")
        
        return papers
    
    def _parse_paper(self, item: Dict[str, Any]) -> Optional[Paper]:
        """Parse CrossRef paper data into Paper model"""
        try:
            # Extract DOI (primary identifier)
            doi = item.get('DOI')
            if not doi:
                return None
            
            # Extract title
            title_list = item.get('title', [])
            title = title_list[0] if title_list else ""
            
            if not title.strip():
                return None
            
            # Extract authors
            authors = []
            author_list = item.get('author', [])
            for author in author_list:
                given = author.get('given', '')
                family = author.get('family', '')
                if family:
                    full_name = f"{given} {family}".strip()
                    authors.append(full_name)
            
            # Extract abstract (often not available in CrossRef)
            abstract = item.get('abstract', '')
            if not abstract:
                abstract = "Abstract not available from CrossRef"
            
            # Extract publication date
            pub_date = None
            if 'published-print' in item:
                date_parts = item['published-print'].get('date-parts', [[]])[0]
            elif 'published-online' in item:
                date_parts = item['published-online'].get('date-parts', [[]])[0]
            elif 'created' in item:
                date_parts = item['created'].get('date-parts', [[]])[0]
            else:
                date_parts = []
            
            if len(date_parts) >= 1:
                try:
                    year = date_parts[0]
                    month = date_parts[1] if len(date_parts) > 1 else 1
                    day = date_parts[2] if len(date_parts) > 2 else 1
                    pub_date = datetime(year, month, day)
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse date parts: {date_parts}")
            
            # Extract venue information
            venue = None
            container_title = item.get('container-title', [])
            if container_title:
                venue = container_title[0]
            
            # Extract citation count (not available in CrossRef, set to 0)
            citations = 0
            
            # Generate URL from DOI
            url = f"https://doi.org/{doi}"
            
            # Create unique ID
            paper_id = f"crossref_{doi.replace('/', '_').replace('.', '_')}"
            
            # Create Paper object
            paper = Paper(
                id=paper_id,
                title=title.strip(),
                authors=authors,
                abstract=abstract,
                url=url,
                published_date=pub_date,
                venue=venue,
                citations=citations,
                doi=doi,
                created_at=datetime.now()
            )
            
            return paper
            
        except Exception as e:
            logger.error(f"Error parsing CrossRef paper: {e}")
            return None
    
    def get_paper_by_doi(self, doi: str) -> Optional[Paper]:
        """Get detailed information about a paper by DOI"""
        try:
            # Clean DOI
            clean_doi = doi.replace('https://doi.org/', '').strip()
            url = f"{self.base_url}/{clean_doi}"
            
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'message' in data:
                return self._parse_paper(data['message'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching paper by DOI from CrossRef: {e}")
            return None
    
    def search_by_author(self, author_name: str, max_results: int = 50) -> List[Paper]:
        """Search papers by author using CrossRef"""
        try:
            params = {
                'query.author': author_name,
                'rows': min(max_results, 1000),
                'sort': 'score',
                'order': 'desc'
            }
            
            self._rate_limit()
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            if 'message' in data and 'items' in data['message']:
                for item in data['message']['items']:
                    paper = self._parse_paper(item)
                    if paper:
                        papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers by author: {author_name}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching by author in CrossRef: {e}")
            return []
    
    def search_by_title(self, title: str) -> Optional[Paper]:
        """Search for a specific paper by title"""
        try:
            params = {
                'query.title': title,
                'rows': 1
            }
            
            self._rate_limit()
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'message' in data and 'items' in data['message'] and data['message']['items']:
                return self._parse_paper(data['message']['items'][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching by title in CrossRef: {e}")
            return None
    
    def get_citation_count(self, doi: str) -> int:
        """Get citation count for a DOI (CrossRef doesn't provide this directly)"""
        # CrossRef doesn't provide citation counts
        # This method is here for interface compatibility but returns 0
        logger.info("Citation counts not available through CrossRef API")
        return 0
    
    def get_references(self, doi: str) -> List[Dict[str, Any]]:
        """Get references cited by a paper"""
        try:
            clean_doi = doi.replace('https://doi.org/', '').strip()
            url = f"{self.base_url}/{clean_doi}"
            
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'message' in data:
                return data['message'].get('reference', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching references from CrossRef: {e}")
            return []
    
    def format_citation_apa(self, paper_data: Dict[str, Any]) -> str:
        """Format a paper citation in APA style using CrossRef data"""
        try:
            # Extract authors
            authors_list = []
            for author in paper_data.get('author', []):
                given = author.get('given', '')
                family = author.get('family', '')
                if family:
                    if given:
                        authors_list.append(f"{family}, {given[0]}.")
                    else:
                        authors_list.append(family)
            
            if not authors_list:
                authors_str = "Unknown Author"
            elif len(authors_list) == 1:
                authors_str = authors_list[0]
            elif len(authors_list) <= 7:
                authors_str = ", ".join(authors_list[:-1]) + f", & {authors_list[-1]}"
            else:
                authors_str = ", ".join(authors_list[:6]) + f", ... {authors_list[-1]}"
            
            # Extract year
            year = "n.d."
            if 'published-print' in paper_data:
                date_parts = paper_data['published-print'].get('date-parts', [[]])[0]
            elif 'published-online' in paper_data:
                date_parts = paper_data['published-online'].get('date-parts', [[]])[0]
            else:
                date_parts = []
            
            if date_parts:
                year = str(date_parts[0])
            
            # Extract title
            title_list = paper_data.get('title', [])
            title = title_list[0] if title_list else "Unknown Title"
            
            # Extract journal
            container_title = paper_data.get('container-title', [])
            journal = container_title[0] if container_title else "Unknown Journal"
            
            # Extract volume and issue
            volume = paper_data.get('volume', '')
            issue = paper_data.get('issue', '')
            
            # Extract pages
            page = paper_data.get('page', '')
            
            # Extract DOI
            doi = paper_data.get('DOI', '')
            
            # Build citation
            citation = f"{authors_str} ({year}). {title}. *{journal}*"
            
            if volume:
                citation += f", *{volume}*"
                if issue:
                    citation += f"({issue})"
            
            if page:
                citation += f", {page}"
            
            if doi:
                citation += f". https://doi.org/{doi}"
            
            return citation
            
        except Exception as e:
            logger.error(f"Error formatting APA citation: {e}")
            return "Error formatting citation"
    
    def format_citation_mla(self, paper_data: Dict[str, Any]) -> str:
        """Format a paper citation in MLA style using CrossRef data"""
        try:
            # Extract first author
            authors = paper_data.get('author', [])
            if authors:
                first_author = authors[0]
                given = first_author.get('given', '')
                family = first_author.get('family', '')
                
                if family and given:
                    author_str = f"{family}, {given}"
                elif family:
                    author_str = family
                else:
                    author_str = "Unknown Author"
                
                if len(authors) > 1:
                    author_str += ", et al."
            else:
                author_str = "Unknown Author"
            
            # Extract title
            title_list = paper_data.get('title', [])
            title = f'"{title_list[0]}"' if title_list else '"Unknown Title"'
            
            # Extract journal
            container_title = paper_data.get('container-title', [])
            journal = f"*{container_title[0]}*" if container_title else "*Unknown Journal*"
            
            # Extract date
            year = "n.d."
            if 'published-print' in paper_data:
                date_parts = paper_data['published-print'].get('date-parts', [[]])[0]
            elif 'published-online' in paper_data:
                date_parts = paper_data['published-online'].get('date-parts', [[]])[0]
            else:
                date_parts = []
            
            if date_parts:
                year = str(date_parts[0])
            
            # Extract DOI for URL
            doi = paper_data.get('DOI', '')
            url = f"https://doi.org/{doi}" if doi else "URL unavailable"
            
            # Build MLA citation
            citation = f"{author_str}. {title} {journal}, {year}, {url}."
            
            return citation
            
        except Exception as e:
            logger.error(f"Error formatting MLA citation: {e}")
            return "Error formatting citation"