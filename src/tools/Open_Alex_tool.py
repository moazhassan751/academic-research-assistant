import requests
import time
import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from ..storage.models import Paper
from ..utils.logging import logger
from ..utils.config import config
from ..utils.performance_optimizer import optimizer, ultra_cache, turbo_batch_processor

class UltraFastOpenAlexTool:
    """Ultra-fast OpenAlex API tool with comprehensive performance optimizations"""
    
    def __init__(self, mailto: str = None):
        self.base_url = "https://api.openalex.org/works"
        self.rate_limit_delay = 0.05  # Reduced from 0.1 for faster processing
        self.last_request_time = 0
        
        # Use provided email or get from config
        self.mailto = mailto or config.get('apis.openalex.mailto', 
                                          config.get('apis.crossref.mailto', 'rmoazhassan555@gmail.com'))
        
        # Enhanced session with performance optimizations
        self.session = requests.Session()
        self.session.timeout = (5, 20)  # Reduced timeouts
        self.session.headers.update({
            'User-Agent': f'AcademicResearchAssistant/2.0 (mailto:{self.mailto})',
            'Accept': 'application/json',
            # Remove problematic Accept-Encoding header
            'Connection': 'keep-alive',  # Connection reuse
            'Cache-Control': 'max-age=300'  # 5-minute cache
        })
        
        # Connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=2,
            pool_block=False
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        
        # Performance tracking
        self.error_counts = defaultdict(int)
        self.request_stats = {'total': 0, 'success': 0, 'cached': 0}
        
        # Async session for concurrent requests
        self._async_session = None
        
        logger.info(f"Ultra-fast OpenAlex tool initialized with email: {self.mailto}")
    
    async def _get_async_session(self):
        """Get or create async HTTP session"""
        if self._async_session is None:
            timeout = aiohttp.ClientTimeout(total=20, connect=5)
            connector = aiohttp.TCPConnector(
                limit=20,
                limit_per_host=10,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            self._async_session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': f'AcademicResearchAssistant/2.0 (mailto:{self.mailto})',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate, br'
                }
            )
        
        return self._async_session
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to the API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any], max_retries: int = 3) -> Optional[Dict]:
        """Make HTTP request with enhanced error handling and retries"""
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                
                # Debug logging with actual constructed URL
                constructed_url = f"{url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
                logger.debug(f"OpenAlex request URL: {constructed_url}")
                logger.debug(f"OpenAlex request params: {params}")
                
                response = self.session.get(url, params=params)
                
                # Log the actual URL that was requested
                logger.debug(f"Actual request URL: {response.url}")
                
                # Handle rate limiting
                if response.status_code == 429:
                    self.error_counts['rate_limits'] += 1
                    retry_after = int(response.headers.get('Retry-After', 10))
                    logger.warning(f"Rate limited by OpenAlex, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                # Handle 403 Forbidden - often due to bad parameters
                if response.status_code == 403:
                    logger.error(f"OpenAlex 403 Forbidden - check parameters: {params}")
                    logger.error(f"Response content: {response.text[:500] if response else 'No response'}")
                    break
                
                response.raise_for_status()
                
                # Check if response has content
                if not response.text.strip():
                    logger.warning("OpenAlex returned empty response")
                    return None
                
                # Try to parse JSON
                try:
                    # Handle potential encoding issues
                    if response.encoding is None:
                        response.encoding = 'utf-8'
                    return response.json()
                except json.JSONDecodeError as json_error:
                    logger.error(f"OpenAlex JSON parsing error: {json_error}")
                    logger.error(f"Response status: {response.status_code}")
                    logger.error(f"Response headers: {dict(response.headers)}")
                    logger.error(f"Response content preview: {response.text[:200] if response.text else 'No content'}")
                    return None
                
            except requests.exceptions.Timeout:
                self.error_counts['timeouts'] += 1
                logger.warning(f"OpenAlex request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
            except requests.exceptions.ConnectionError as e:
                self.error_counts['connection_errors'] += 1
                error_msg = str(e).lower()
                if any(term in error_msg for term in ["dns", "getaddrinfo", "name resolution", "11001"]):
                    logger.warning(f"OpenAlex DNS resolution error (attempt {attempt + 1}/{max_retries}): {e}")
                else:
                    logger.warning(f"OpenAlex connection error (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(min(30, 2 ** attempt))  # Cap backoff at 30 seconds
                    continue
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [500, 502, 503, 504]:
                    logger.warning(f"OpenAlex server error {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                elif e.response.status_code == 400:
                    logger.error(f"OpenAlex 400 Bad Request - invalid parameters")
                    logger.error(f"Request URL: {response.url}")
                    logger.error(f"Request params: {params}")
                    logger.error(f"Response content: {e.response.text[:500] if e.response else 'No response'}")
                    break
                else:
                    logger.error(f"OpenAlex HTTP error: {e}")
                    logger.error(f"Request URL: {response.url if 'response' in locals() else 'Unknown'}")
                    logger.error(f"Response content: {e.response.text[:500] if e.response else 'No response'}")
                    break
                    
            except Exception as e:
                logger.error(f"Unexpected OpenAlex error: {e}")
                break
        
        return None
    
    def search_papers(self, query: str, max_results: int = 50, 
                     date_from: Optional[datetime] = None) -> List[Paper]:
        """Search papers using OpenAlex API with enhanced error handling"""
        papers = []
        
        if not query or not isinstance(query, str) or not query.strip():
            logger.warning("Empty or invalid query provided to OpenAlex search")
            return papers
        
        # Sanitize query to prevent bad requests
        query = query.strip()
        
        # Remove problematic characters that can cause 400 errors
        import re
        query = re.sub(r'[^\w\s\-\.\(\)\"\':]', ' ', query)
        query = ' '.join(query.split())  # Normalize whitespace
        
        if len(query) < 2:
            logger.warning(f"Query too short for OpenAlex: '{query}'")
            return papers
        
        # Validate max_results - OpenAlex doesn't accept 0
        if max_results <= 0:
            logger.warning(f"Invalid max_results: {max_results}, setting to 50")
            max_results = 50
        
        try:
            # CRITICAL FIX: Set per-page to a valid positive integer
            per_page = min(max_results, 200)  # OpenAlex max is 200 per page
            
            # Prepare search parameters with proper URL encoding
            from urllib.parse import quote_plus
            
            # Format query for OpenAlex filter parameter
            search_query = query.replace(' ', '+')
            
            params = {
                'filter': f'display_name.search:{search_query}',  # FIXED: Use proper OpenAlex filter format
                'per-page': per_page,  # FIXED: Never set to 0
                'sort': 'cited_by_count:desc',
                'mailto': self.mailto
            }
            
            # Use a more conservative select to avoid 403 errors
            select_fields = [
                'id',
                'title', 
                'authorships',
                'publication_date',
                'primary_location',
                'cited_by_count',
                'doi',
                'type'
                # Removed abstract_inverted_index to avoid encoding issues
            ]
            params['select'] = ','.join(select_fields)
            
            # Add date filter if specified - combine with search filter
            if date_from and isinstance(date_from, datetime):
                date_str = date_from.strftime('%Y-%m-%d')
                # Combine search and date filters using comma separation
                existing_filter = params.get('filter', '')
                if existing_filter:
                    params['filter'] = f'{existing_filter},publication_date:>{date_str}'
                else:
                    params['filter'] = f'publication_date:>{date_str}'
            
            logger.info(f"Searching OpenAlex for: {query} (max: {max_results})")
            
            # Make request with enhanced error handling
            data = self._make_request(self.base_url, params)
            
            if not data:
                logger.error("No response data from OpenAlex")
                self.error_counts['empty_responses'] += 1
                return papers
            
            # Check for error in response
            if 'error' in data:
                logger.error(f"OpenAlex API error: {data.get('error')}")
                return papers
            
            results = data.get('results', [])
            logger.info(f"OpenAlex returned {len(results)} results")
            
            if not results:
                logger.debug("No results found in OpenAlex response")
                self.error_counts['empty_responses'] += 1
                return papers
            
            # Process results with detailed error tracking and validation
            successful_parses = 0
            failed_parses = 0
            
            for i, item in enumerate(results[:max_results]):
                try:
                    if not item or not isinstance(item, dict):
                        failed_parses += 1
                        logger.debug(f"Invalid item {i+1}: not a dictionary")
                        continue
                    
                    paper = self.parse_paper(item)
                    if paper:
                        papers.append(paper)
                        successful_parses += 1
                    else:
                        failed_parses += 1
                        
                except Exception as e:
                    failed_parses += 1
                    self.error_counts['parsing_errors'] += 1
                    logger.debug(f"Error parsing paper {i+1}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(papers)} papers from OpenAlex (successful: {successful_parses}, failed: {failed_parses})")
            
        except Exception as e:
            logger.error(f"Unexpected error in OpenAlex search: {e}")
            self.error_counts['parsing_errors'] += 1
        
        return papers
    
    def parse_paper(self, item: Dict[str, Any]) -> Optional[Paper]:
        """Parse OpenAlex paper data into Paper model with comprehensive error handling"""
        try:
            # Validate input with detailed logging
            if not isinstance(item, dict) or not item:
                return None
            
            # Extract and validate OpenAlex ID
            openalex_id = ''
            raw_id = item.get('id')
            
            if not raw_id:
                return None
            
            try:
                if isinstance(raw_id, str):
                    if '/' in raw_id:
                        openalex_id = raw_id.split('/')[-1]
                    else:
                        openalex_id = raw_id
                else:
                    openalex_id = str(raw_id)
                
                # Clean the ID
                openalex_id = openalex_id.replace('W', '') if openalex_id.startswith('W') else openalex_id
                
                if not openalex_id or openalex_id.lower() in ['none', 'null', '']:
                    return None
                    
            except Exception:
                return None
            
            # Extract and validate title
            title = item.get('title')
            if not title:
                return None
            
            try:
                if isinstance(title, str):
                    title = title.strip()
                else:
                    title = str(title).strip()
                
                if not title or len(title) < 3:
                    return None
                    
            except Exception:
                return None
            
            # Extract authors
            authors = []
            try:
                authorships = item.get('authorships', [])
                if isinstance(authorships, list):
                    for authorship in authorships:
                        if not isinstance(authorship, dict):
                            continue
                        
                        author = authorship.get('author', {})
                        if not isinstance(author, dict):
                            continue
                        
                        display_name = author.get('display_name')
                        if display_name and isinstance(display_name, str):
                            clean_name = display_name.strip()
                            if clean_name and len(clean_name) >= 2:
                                authors.append(clean_name)
                                
                authors = authors[:20]  # Limit to 20 authors
                
            except Exception:
                pass
            
            # Extract abstract
            abstract = ""
            try:
                abstract_index = item.get('abstract_inverted_index')
                if abstract_index and isinstance(abstract_index, dict):
                    abstract = self._reconstruct_abstract(abstract_index)
                
                if not abstract or len(abstract.strip()) < 20:
                    alt_abstract = item.get('abstract')
                    if alt_abstract and isinstance(alt_abstract, str):
                        abstract = alt_abstract.strip()
                
                if abstract:
                    abstract = ' '.join(abstract.split())
                    if len(abstract) > 2000:
                        abstract = abstract[:2000] + "..."
                else:
                    abstract = "Abstract not available"
                    
            except Exception:
                abstract = "Abstract not available"
            
            # Extract publication date
            pub_date = None
            try:
                pub_date_str = item.get('publication_date')
                if pub_date_str and isinstance(pub_date_str, str):
                    date_formats = ['%Y-%m-%d', '%Y-%m', '%Y']
                    for fmt in date_formats:
                        try:
                            pub_date = datetime.strptime(pub_date_str[:len(fmt)], fmt)
                            if pub_date.year < 1800 or pub_date.year > datetime.now().year + 1:
                                pub_date = None
                                continue
                            break
                        except ValueError:
                            continue
                            
            except Exception:
                pass
            
            # Extract venue information
            venue = None
            try:
                primary_location = item.get('primary_location')
                if isinstance(primary_location, dict):
                    source = primary_location.get('source')
                    if isinstance(source, dict):
                        venue_name = source.get('display_name')
                        if venue_name and isinstance(venue_name, str):
                            venue = venue_name.strip()
                            if venue.lower() in ['none', 'null', '', 'unknown']:
                                venue = None
                            elif len(venue) > 200:
                                venue = venue[:200] + "..."
                                
            except Exception:
                pass
            
            # Extract citations
            citations = 0
            try:
                citation_count = item.get('cited_by_count', 0)
                if isinstance(citation_count, (int, float)):
                    citations = max(0, int(citation_count))
                elif isinstance(citation_count, str) and citation_count.isdigit():
                    citations = max(0, int(citation_count))
                    
            except Exception:
                citations = 0
            
            # Handle DOI
            doi = None
            try:
                raw_doi = item.get('doi')
                if raw_doi and isinstance(raw_doi, str):
                    clean_doi = raw_doi.replace('https://doi.org/', '').strip()
                    if clean_doi and '/' in clean_doi and len(clean_doi) >= 7:
                        doi = clean_doi
                        
            except Exception:
                pass
            
            # Generate URL
            url = None
            try:
                if raw_id and isinstance(raw_id, str) and raw_id.startswith('http'):
                    url = raw_id
                else:
                    url = f"https://openalex.org/W{openalex_id}"
                    
            except Exception:
                url = f"https://openalex.org/W{openalex_id}"
            
            # Create Paper object
            try:
                paper = Paper(
                    id=f"openalex_{openalex_id}",
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
                
                # Add source tracking
                paper.source = 'openalex'
                
                return paper
                
            except Exception as e:
                logger.error(f"Error creating Paper object for {openalex_id}: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Unexpected error parsing OpenAlex paper: {e}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """Reconstruct abstract text from OpenAlex inverted index"""
        if not inverted_index or not isinstance(inverted_index, dict):
            return ""
        
        try:
            word_positions = []
            
            for word, positions in inverted_index.items():
                if not word or not isinstance(word, str):
                    continue
                if not positions or not isinstance(positions, list):
                    continue
                
                clean_word = word.strip()
                if not clean_word or len(clean_word) > 50:
                    continue
                
                for pos in positions:
                    try:
                        if isinstance(pos, (int, float)):
                            position = int(pos)
                            if 0 <= position < 10000:
                                word_positions.append((position, clean_word))
                    except (ValueError, TypeError):
                        continue
            
            if not word_positions:
                return ""
            
            word_positions.sort(key=lambda x: x[0])
            abstract_words = [word for _, word in word_positions]
            
            if not abstract_words:
                return ""
            
            abstract = ' '.join(abstract_words)
            abstract = ' '.join(abstract.split())
            
            if len(abstract) > 3000:
                abstract = abstract[:3000] + "..."
            elif len(abstract) < 10:
                return ""
            
            return abstract
                
        except Exception:
            return ""
    
    def get_paper_details(self, openalex_id: str) -> Optional[Paper]:
        """Get detailed information about a specific paper"""
        if not openalex_id or not isinstance(openalex_id, str):
            return None
        
        try:
            clean_id = openalex_id.replace('openalex_', '').replace('W', '')
            if not clean_id:
                return None
            
            url = f"https://api.openalex.org/works/W{clean_id}"
            params = {
                'select': 'id,title,authorships,abstract_inverted_index,publication_date,primary_location,cited_by_count,doi,type',
                'mailto': self.mailto
            }
            
            data = self._make_request(url, params)
            
            if data:
                return self.parse_paper(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching paper details from OpenAlex: {e}")
            return None
    
    def search_by_author(self, author_name: str, max_results: int = 50) -> List[Paper]:
        """Search papers by author using OpenAlex"""
        if not author_name or not isinstance(author_name, str) or not author_name.strip():
            return []
        
        try:
            # First find the author
            authors_url = "https://api.openalex.org/authors"
            author_params = {
                'search': author_name.strip(),
                'per-page': 5,
                'select': 'id,display_name,works_count',
                'mailto': self.mailto
            }
            
            author_data = self._make_request(authors_url, author_params)
            
            if not author_data or 'results' not in author_data:
                return []
            
            authors = author_data.get('results', [])
            if not authors:
                return []
            
            # Take the first author
            target_author = authors[0]
            author_id = target_author.get('id', '').split('/')[-1] if target_author.get('id') else ''
            
            if not author_id:
                return []
            
            # Get works by this author
            works_params = {
                'filter': f'author.id:{author_id}',
                'per-page': min(max_results, 200),
                'sort': 'cited_by_count:desc',
                'select': 'id,title,authorships,abstract_inverted_index,publication_date,primary_location,cited_by_count,doi,type',
                'mailto': self.mailto
            }
            
            works_data = self._make_request(self.base_url, works_params)
            papers = []
            
            if works_data and 'results' in works_data:
                for item in works_data['results']:
                    paper = self.parse_paper(item)
                    if paper:
                        papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching by author in OpenAlex: {e}")
            return []
    
    def search_by_doi(self, doi: str) -> Optional[Paper]:
        """Search for a paper by DOI"""
        if not doi or not isinstance(doi, str):
            return None
        
        try:
            clean_doi = doi.replace('https://doi.org/', '').strip()
            
            if not clean_doi or '/' not in clean_doi:
                return None
            
            params = {
                'filter': f'doi:{clean_doi}',
                'select': 'id,title,authorships,abstract_inverted_index,publication_date,primary_location,cited_by_count,doi,type',
                'mailto': self.mailto,
                'per-page': 1
            }
            
            data = self._make_request(self.base_url, params)
            
            if data and data.get('results'):
                return self.parse_paper(data['results'][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching by DOI in OpenAlex: {e}")
            return None
    
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
            'empty_responses': 0
        }


# Backward compatibility alias
class OpenAlexTool(UltraFastOpenAlexTool):
    """Legacy alias for backward compatibility"""
    pass