import requests
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..storage.models import Paper
from ..utils.config import config
from ..utils.logging import logger

class SemanticScholarTool:
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        # DO NOT use API key - use public endpoint only
        self.api_key = None
        self.rate_limit = 100  # requests per 5 minutes for public API
        self.last_request_time = 0
        self.min_request_interval = 3  # 3 seconds between requests to be safe
        
        # Public API headers (no authentication required)
        self.headers = {
            'User-Agent': 'Academic Research Assistant/1.0 (research@example.com)',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Remove any API key usage
        logger.info("Using Semantic Scholar public API (no authentication)")
    
    def _wait_for_rate_limit(self):
        """Implement rate limiting for API requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_papers(self, query: str, limit: int = 50, 
                     fields: List[str] = None, year: str = None) -> List[Paper]:
        """Search papers using Semantic Scholar public API"""
        if fields is None:
            fields = ['paperId', 'title', 'authors', 'abstract', 'url', 
                     'publicationDate', 'venue', 'citationCount', 'doi', 
                     'externalIds', 'publicationTypes']
        
        try:
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}/paper/search"
            params = {
                'query': query,
                'limit': min(limit, 100),  # API limit is 100
                'fields': ','.join(fields)
            }
            
            # Add year filter if provided
            if year:
                params['year'] = year
            
            logger.debug(f"Requesting: {url} with params: {params}")
            
            # Use public API without authentication
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            # Handle different response codes
            if response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                return []  # Don't retry to avoid infinite loops
            elif response.status_code == 403:
                logger.warning("Access forbidden - using public API without key")
                return []
            elif response.status_code == 400:
                logger.error(f"Bad request - check query format: {response.text}")
                return []
            elif response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return []
            
            data = response.json()
            papers = []
            
            for item in data.get('data', []):
                try:
                    # Parse publication date
                    published_date = None
                    if item.get('publicationDate'):
                        try:
                            published_date = datetime.strptime(
                                item['publicationDate'], '%Y-%m-%d'
                            )
                        except ValueError:
                            # Try alternative date formats
                            for fmt in ['%Y', '%Y-%m']:
                                try:
                                    published_date = datetime.strptime(
                                        item['publicationDate'], fmt
                                    )
                                    break
                                except ValueError:
                                    continue
                    
                    # Extract author names safely
                    authors = []
                    if item.get('authors'):
                        for author in item['authors']:
                            if isinstance(author, dict) and author.get('name'):
                                authors.append(author['name'])
                            elif isinstance(author, str):
                                authors.append(author)
                    
                    # Create paper object with required fields
                    paper = Paper(
                        id=f"s2_{item['paperId']}",
                        title=item.get('title', '').strip(),
                        authors=authors,
                        abstract=item.get('abstract', ''),
                        url=item.get('url', ''),
                        published_date=published_date,
                        venue=item.get('venue', ''),
                        citations=item.get('citationCount', 0),
                        doi=item.get('doi')
                    )
                    
                    # Only add papers with meaningful content
                    if paper.title and (paper.abstract or paper.authors):
                        papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Error parsing paper data: {e}")
                    continue
            
            logger.info(f"Found {len(papers)} papers on Semantic Scholar for: {query}")
            return papers
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout for Semantic Scholar API")
            return []
        except requests.exceptions.ConnectionError:
            logger.error("Connection error for Semantic Scholar API")
            return []
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {e}")
            return []
    
    def get_paper_details(self, paper_id: str, fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get detailed information about a paper"""
        if fields is None:
            fields = ['paperId', 'title', 'authors', 'abstract', 'citations', 
                     'references', 'venue', 'year', 'doi', 'externalIds']
        
        try:
            self._wait_for_rate_limit()
            
            # Remove 's2_' prefix if present
            clean_paper_id = paper_id.replace('s2_', '')
            
            url = f"{self.base_url}/paper/{clean_paper_id}"
            params = {'fields': ','.join(fields)}
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Paper not found: {paper_id}")
                return None
            else:
                logger.error(f"Error getting paper details: {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"Error getting paper details {paper_id}: {e}")
            return None
    
    def get_citations(self, paper_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get citations for a paper"""
        try:
            self._wait_for_rate_limit()
            
            clean_paper_id = paper_id.replace('s2_', '')
            url = f"{self.base_url}/paper/{clean_paper_id}/citations"
            params = {
                'limit': min(limit, 1000),
                'fields': 'paperId,title,authors,year,venue'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                logger.error(f"Error getting citations: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting citations for {paper_id}: {e}")
            return []
    
    def search_by_author(self, author_name: str, limit: int = 50) -> List[Paper]:
        """Search papers by author name"""
        query = f"author:{author_name}"
        return self.search_papers(query, limit)
    
    def search_recent_papers(self, query: str, years_back: int = 2, limit: int = 50) -> List[Paper]:
        """Search for recent papers within specified years"""
        current_year = datetime.now().year
        year_range = f"{current_year - years_back}-{current_year}"
        return self.search_papers(query, limit, year=year_range)