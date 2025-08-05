import requests
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..storage.models import Paper
from ..utils.config import config
from ..utils.logging import logger

class SemanticScholarTool:
    def __init__(self):
        self.base_url = config.get('apis.semantic_scholar.base_url')
        self.api_key = config.api_keys.get('semantic_scholar')
        self.rate_limit = config.get('apis.semantic_scholar.rate_limit', 100)
        
        self.headers = {'User-Agent': 'Academic Research Assistant'}
        if self.api_key:
            self.headers['x-api-key'] = self.api_key
    
    def search_papers(self, query: str, limit: int = 50, 
                     fields: List[str] = None) -> List[Paper]:
        """Search papers using Semantic Scholar API"""
        if fields is None:
            fields = ['paperId', 'title', 'authors', 'abstract', 'url', 
                     'publicationDate', 'venue', 'citationCount', 'doi']
        
        try:
            url = f"{self.base_url}/paper/search"
            params = {
                'query': query,
                'limit': limit,
                'fields': ','.join(fields)
            }
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for item in data.get('data', []):
                try:
                    published_date = None
                    if item.get('publicationDate'):
                        published_date = datetime.strptime(
                            item['publicationDate'], '%Y-%m-%d'
                        )
                    
                    paper = Paper(
                        id=f"s2_{item['paperId']}",
                        title=item.get('title', ''),
                        authors=[author.get('name', '') for author in item.get('authors', [])],
                        abstract=item.get('abstract', ''),
                        url=item.get('url', ''),
                        published_date=published_date,
                        venue=item.get('venue', ''),
                        citations=item.get('citationCount', 0),
                        doi=item.get('doi')
                    )
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Error parsing paper data: {e}")
                    continue
            
            logger.info(f"Found {len(papers)} papers on Semantic Scholar for: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {e}")
            return []
    
    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a paper"""
        try:
            url = f"{self.base_url}/paper/{paper_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting paper details {paper_id}: {e}")
            return None