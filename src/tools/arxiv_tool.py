import arxiv
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..storage.models import Paper
from ..utils.config import config
from ..utils.logging import logger

class ArxivTool:
    def __init__(self):
        self.client = arxiv.Client()
        self.max_results = config.get('apis.arxiv.max_results', 100)
        self.delay = config.get('apis.arxiv.delay', 3)
    
    def search_papers(self, query: str, max_results: Optional[int] = None, 
                     date_from: Optional[datetime] = None) -> List[Paper]:
        """Search papers on arXiv"""
        if max_results is None:
            max_results = self.max_results
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            for result in self.client.results(search):
                # Filter by date if specified
                if date_from and result.published < date_from:
                    continue
                
                paper = Paper(
                    id=f"arxiv_{result.entry_id.split('/')[-1]}",
                    title=result.title,
                    authors=[str(author) for author in result.authors],
                    abstract=result.summary,
                    url=result.entry_id,
                    published_date=result.published,
                    venue="arXiv",
                    arxiv_id=result.entry_id.split('/')[-1],
                    pdf_path=result.pdf_url if hasattr(result, 'pdf_url') else None
                )
                papers.append(paper)
                
                # Respect rate limiting
                time.sleep(self.delay)
            
            logger.info(f"Found {len(papers)} papers on arXiv for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Paper]:
        """Get a specific paper by arXiv ID"""
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(self.client.results(search))
            
            if not results:
                return None
            
            result = results[0]
            return Paper(
                id=f"arxiv_{arxiv_id}",
                title=result.title,
                authors=[str(author) for author in result.authors],
                abstract=result.summary,
                url=result.entry_id,
                published_date=result.published,
                venue="arXiv",
                arxiv_id=arxiv_id,
                pdf_path=result.pdf_url if hasattr(result, 'pdf_url') else None
            )
            
        except Exception as e:
            logger.error(f"Error getting arXiv paper {arxiv_id}: {e}")
            return None