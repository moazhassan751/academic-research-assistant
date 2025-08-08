import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote_plus, urlencode
from ..storage.models import Paper
from ..utils.logging import logger
from ..utils.config import config

class CrossRefTool:
    def __init__(self):
        self.base_url = "https://api.crossref.org/works"
        self.rate_limit_delay = 1.5  # Respectful rate limiting
        self.last_request_time = 0
        self.session = requests.Session()
        
        # Enhanced request configuration
        self.session.timeout = (15, 45)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        
        # Set user agent with mailto for politeness policy
        mailto = config.get('apis.crossref.mailto', 'rmoazhassan555@gmail.com')
        self.session.headers.update({
            'User-Agent': f'AcademicResearchAssistant/1.0 (mailto:{mailto})'
        })
        
        # Error tracking
        self.error_counts = {
            'rate_limits': 0,
            'timeouts': 0,
            'connection_errors': 0,
            'parsing_errors': 0,
            'bad_requests': 0
        }
        
        logger.info("CrossRef tool initialized")
    
    def _rate_limit(self):
        """Implement respectful rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any], max_retries: int = 3) -> Optional[Dict]:
        """FIXED: Make HTTP request with corrected parameter handling"""
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                
                # FIXED: Clean parameters and avoid problematic ones
                clean_params = {}
                for key, value in params.items():
                    if value is not None and str(value).strip():
                        # FIXED: Skip the 'select' parameter that causes 400 errors
                        if key == 'select':
                            logger.debug("Skipping 'select' parameter to avoid 400 error")
                            continue
                        clean_params[key] = str(value).strip()
                
                logger.debug(f"CrossRef request: {url} with params: {clean_params}")
                
                response = self.session.get(url, params=clean_params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    self.error_counts['rate_limits'] += 1
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited by CrossRef, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                # Handle 400 Bad Request
                if response.status_code == 400:
                    self.error_counts['bad_requests'] += 1
                    logger.error(f"CrossRef Bad Request (400): {response.text[:200]}")
                    # Try with minimal parameters
                    if clean_params and len(clean_params) > 1:
                        minimal_params = {'query': clean_params.get('query', '')}
                        logger.info("Retrying with minimal parameters")
                        response = self.session.get(url, params=minimal_params)
                        if response.status_code == 200:
                            return response.json()
                    return None
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                self.error_counts['timeouts'] += 1
                logger.warning(f"CrossRef timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                
            except requests.exceptions.ConnectionError:
                self.error_counts['connection_errors'] += 1
                logger.warning(f"CrossRef connection error (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                    
            except requests.exceptions.HTTPError as e:
                if e.response and e.response.status_code in [500, 502, 503, 504]:
                    logger.warning(f"CrossRef server error {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                else:
                    logger.error(f"CrossRef HTTP error: {e}")
                    break
                    
            except Exception as e:
                logger.error(f"Unexpected CrossRef error: {e}")
                break
        
        return None
    
    def search_papers(self, query: str, max_results: int = 50, 
                     date_from: Optional[datetime] = None) -> List[Paper]:
        """FIXED: Search papers without problematic parameters"""
        papers = []
        
        if not query or not query.strip():
            logger.warning("Empty query provided to CrossRef search")
            return papers
        
        try:
            # FIXED: Use only basic, safe parameters that don't cause 400 errors
            params = {
                'query': query.strip(),
                'rows': min(max_results, 1000),  # CrossRef max is 1000
                'sort': 'score',
                'order': 'desc'
            }
            
            # FIXED: Don't use 'select' parameter as it causes validation errors
            # The API will return all available fields by default
            
            # Add date filter if specified
            if date_from:
                year = date_from.year
                params['filter'] = f'from-pub-date:{year}'
            
            logger.info(f"Searching CrossRef for: {query} (max: {max_results})")
            
            # Make request
            data = self._make_request(self.base_url, params)
            
            if not data:
                logger.error("No response data from CrossRef")
                return papers
            
            if 'message' not in data or 'items' not in data['message']:
                logger.warning("No items found in CrossRef response")
                return papers
            
            # Process results
            items = data['message']['items']
            successful_parses = 0
            failed_parses = 0
            
            for item in items[:max_results]:
                try:
                    paper = self._parse_paper(item)
                    if paper:
                        papers.append(paper)
                        successful_parses += 1
                    else:
                        failed_parses += 1
                except Exception as e:
                    failed_parses += 1
                    self.error_counts['parsing_errors'] += 1
                    logger.debug(f"Error parsing CrossRef paper: {e}")
                    continue
            
            logger.info(f"Retrieved {len(papers)} papers from CrossRef (parsed: {successful_parses}, failed: {failed_parses})")
            
        except Exception as e:
            logger.error(f"Error in CrossRef search: {e}")
        
        return papers
    
    def _parse_paper(self, item: Dict[str, Any]) -> Optional[Paper]:
        """Enhanced paper parsing with better error handling"""
        try:
            if not isinstance(item, dict) or not item:
                return None
            
            # Extract DOI
            doi = item.get('DOI')
            if not doi or not isinstance(doi, str) or not doi.strip():
                return None
            doi = doi.strip()
            
            # Extract title
            title_list = item.get('title', [])
            if not title_list or not isinstance(title_list, list):
                return None
            
            title = title_list[0] if title_list else ""
            if not isinstance(title, str):
                title = str(title)
            
            title = title.strip()
            if not title or len(title) < 3:
                return None
            
            # Extract authors
            authors = []
            try:
                author_list = item.get('author', [])
                if isinstance(author_list, list):
                    for author in author_list[:10]:  # Limit authors
                        if not isinstance(author, dict):
                            continue
                        
                        given = author.get('given', '').strip()
                        family = author.get('family', '').strip()
                        
                        if family:
                            if given:
                                full_name = f"{given} {family}".strip()
                            else:
                                full_name = family
                            
                            if full_name and len(full_name) > 1:
                                authors.append(full_name)
            except Exception as e:
                logger.debug(f"Error parsing authors for DOI {doi}: {e}")
            
            # Abstract - CrossRef usually doesn't provide abstracts
            abstract = "Abstract not available from CrossRef"
            
            # Extract publication date
            pub_date = None
            try:
                date_sources = ['published-print', 'published-online', 'published', 'deposited']
                
                for source in date_sources:
                    if source in item:
                        date_info = item[source]
                        if isinstance(date_info, dict) and 'date-parts' in date_info:
                            date_parts = date_info.get('date-parts', [[]])[0] if date_info.get('date-parts') else []
                            if date_parts and isinstance(date_parts, list) and len(date_parts) >= 1:
                                try:
                                    year = int(date_parts[0])
                                    month = int(date_parts[1]) if len(date_parts) > 1 and date_parts[1] else 1
                                    day = int(date_parts[2]) if len(date_parts) > 2 and date_parts[2] else 1
                                    
                                    if 1900 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                                        pub_date = datetime(year, month, day)
                                        break
                                except (ValueError, IndexError, TypeError):
                                    continue
                
            except Exception as e:
                logger.debug(f"Error parsing publication date for DOI {doi}: {e}")
            
            # Extract venue
            venue = None
            try:
                container_title = item.get('container-title', [])
                if container_title and isinstance(container_title, list) and container_title[0]:
                    venue_name = container_title[0]
                    if isinstance(venue_name, str) and venue_name.strip():
                        venue = venue_name.strip()[:200]
            except Exception as e:
                logger.debug(f"Error parsing venue for DOI {doi}: {e}")
            
            # Citation count - use is-referenced-by-count if available
            citations = 0
            try:
                ref_count = item.get('is-referenced-by-count', 0)
                if isinstance(ref_count, (int, float)) and ref_count >= 0:
                    citations = int(ref_count)
            except Exception:
                citations = 0
            
            # Generate URL and ID
            url = f"https://doi.org/{doi}"
            paper_id = f"crossref_{doi.replace('/', '_').replace('.', '_')}"
            
            # Create Paper object
            paper = Paper(
                id=paper_id,
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                published_date=pub_date,
                venue=venue,
                citations=citations,
                doi=doi,
                created_at=datetime.now()
            )
            
            paper.source = 'crossref'
            return paper
                
        except Exception as e:
            logger.error(f"Unexpected error parsing CrossRef paper: {e}")
            return None
    
    def get_paper_by_doi(self, doi: str) -> Optional[Paper]:
        """FIXED: Get paper by DOI without problematic select parameter"""
        if not doi or not isinstance(doi, str):
            return None
        
        try:
            # Clean DOI
            clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '').strip()
            if not clean_doi:
                return None
            
            # FIXED: Use URL without select parameter
            url = f"{self.base_url}/{clean_doi}"
            params = {}  # No parameters to avoid 400 errors
            
            data = self._make_request(url, params)
            
            if data and 'message' in data:
                return self._parse_paper(data['message'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching paper by DOI from CrossRef: {e}")
            return None
    
    def search_by_author(self, author_name: str, max_results: int = 50) -> List[Paper]:
        """FIXED: Search by author without select parameter"""
        if not author_name or not isinstance(author_name, str) or not author_name.strip():
            return []
        
        try:
            params = {
                'query.author': author_name.strip(),
                'rows': min(max_results, 1000),
                'sort': 'score',
                'order': 'desc'
                # FIXED: No select parameter
            }
            
            data = self._make_request(self.base_url, params)
            papers = []
            
            if data and 'message' in data and 'items' in data['message']:
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
        """FIXED: Search by title without select parameter"""
        if not title or not isinstance(title, str) or not title.strip():
            return None
        
        try:
            params = {
                'query.title': title.strip(),
                'rows': 5
                # FIXED: No select parameter
            }
            
            data = self._make_request(self.base_url, params)
            
            if data and 'message' in data and 'items' in data['message']:
                items = data['message']['items']
                
                # Try exact match first
                for item in items:
                    item_title = item.get('title', [''])[0] if item.get('title') else ''
                    if item_title.lower().strip() == title.lower().strip():
                        return self._parse_paper(item)
                
                # Return first valid result
                for item in items:
                    paper = self._parse_paper(item)
                    if paper:
                        return paper
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching by title in CrossRef: {e}")
            return None
    
    def get_citation_count(self, doi: str) -> int:
        """Get citation count for a DOI"""
        if not doi or not isinstance(doi, str):
            return 0
        
        try:
            paper = self.get_paper_by_doi(doi)
            if paper and hasattr(paper, 'citations'):
                return paper.citations
            return 0
        except Exception as e:
            logger.debug(f"Error getting citation count for DOI {doi}: {e}")
            return 0
    
    def format_citation_apa(self, paper_data: Dict[str, Any]) -> str:
        """Enhanced APA citation formatting"""
        try:
            if not isinstance(paper_data, dict):
                return "Invalid paper data for APA citation"
            
            # Extract authors
            authors_list = []
            author_data = paper_data.get('author', [])
            
            if isinstance(author_data, list):
                for author in author_data[:10]:  # Limit authors
                    if not isinstance(author, dict):
                        continue
                    
                    given = author.get('given', '').strip()
                    family = author.get('family', '').strip()
                    
                    if family:
                        if given:
                            # Create initials properly
                            initials = []
                            for name_part in given.split():
                                if name_part and name_part[0].isalpha():
                                    initials.append(f"{name_part[0].upper()}.")
                            given_initials = " ".join(initials)
                            authors_list.append(f"{family}, {given_initials}")
                        else:
                            authors_list.append(family)
            
            # Format author string
            if not authors_list:
                authors_str = "Unknown Author"
            elif len(authors_list) == 1:
                authors_str = authors_list[0]
            elif len(authors_list) == 2:
                authors_str = f"{authors_list[0]}, & {authors_list[1]}"
            else:
                authors_str = ", ".join(authors_list[:-1]) + f", & {authors_list[-1]}"
            
            # Extract year
            year = "n.d."
            date_sources = ['published-print', 'published-online', 'published']
            
            for source in date_sources:
                if source in paper_data:
                    date_info = paper_data[source]
                    if isinstance(date_info, dict) and 'date-parts' in date_info:
                        date_parts = date_info['date-parts']
                        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list):
                            try:
                                year_val = int(date_parts[0][0])
                                if 1900 <= year_val <= 2030:
                                    year = str(year_val)
                                    break
                            except (ValueError, IndexError, TypeError):
                                continue
            
            # Extract title
            title_list = paper_data.get('title', [])
            if isinstance(title_list, list) and title_list:
                title = str(title_list[0]).strip()
                if not title.endswith('.'):
                    title += '.'
            else:
                title = "Unknown Title."
            
            # Extract journal
            container_title = paper_data.get('container-title', [])
            if isinstance(container_title, list) and container_title:
                journal = str(container_title[0]).strip()
            else:
                journal = "Unknown Journal"
            
            # Build citation
            citation = f"{authors_str} ({year}). {title} *{journal}*"
            
            # Add DOI if available
            doi = paper_data.get('DOI', '').strip()
            if doi:
                citation += f". https://doi.org/{doi}"
            
            return citation
            
        except Exception as e:
            logger.error(f"Error formatting APA citation: {e}")
            return f"Citation formatting error: {str(e)}"
    
    def get_error_statistics(self) -> Dict[str, int]:
        """Get error statistics for monitoring"""
        return self.error_counts.copy()
    
    def reset_error_statistics(self):
        """Reset error statistics"""
        self.error_counts = {
            'rate_limits': 0,
            'timeouts': 0,
            'connection_errors': 0,
            'parsing_errors': 0,
            'bad_requests': 0
        }