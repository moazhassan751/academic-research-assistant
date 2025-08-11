"""
Async API processing for Academic Research Assistant
"""

import asyncio
import aiohttp
import time
import logging
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import backoff
from ..storage.models import Paper

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """Supported API providers"""
    OPENALEX = "openalex"
    CROSSREF = "crossref"
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"


@dataclass
class APIRequest:
    """API request configuration"""
    provider: APIProvider
    endpoint: str
    params: Dict[str, Any]
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30


@dataclass
class APIResponse:
    """API response wrapper"""
    provider: APIProvider
    data: Any
    status_code: int
    response_time: float
    error: Optional[str] = None
    success: bool = True


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls_per_second: float = None, requests_per_second: float = None):
        # Support both parameter names for compatibility
        if calls_per_second is not None:
            self.calls_per_second = calls_per_second
        elif requests_per_second is not None:
            self.calls_per_second = requests_per_second
        else:
            self.calls_per_second = 1.0
            
        self.min_interval = 1.0 / self.calls_per_second
        self.last_called = 0.0
    
    async def acquire(self):
        """Wait if necessary to respect rate limit"""
        now = time.time()
        elapsed = now - self.last_called
        
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            await asyncio.sleep(wait_time)
        
        self.last_called = time.time()


class CircuitBreaker:
    """Circuit breaker pattern for API resilience"""
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset circuit breaker"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = 'closed'
    
    def _on_failure(self):
        """Handle failure - potentially open circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'


class AsyncAPIManager:
    """Async API manager with rate limiting, circuit breaking, and concurrent processing"""
    
    def __init__(self, max_concurrent_requests: int = 10):
        self.max_concurrent_requests = max_concurrent_requests
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiters for different providers
        self.rate_limiters = {
            APIProvider.OPENALEX: RateLimiter(calls_per_second=1.0),
            APIProvider.CROSSREF: RateLimiter(calls_per_second=0.5),
            APIProvider.ARXIV: RateLimiter(calls_per_second=0.5),
            APIProvider.SEMANTIC_SCHOLAR: RateLimiter(calls_per_second=1.0),
        }
        
        # Circuit breakers for reliability
        self.circuit_breakers = {
            provider: CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=60,
                expected_exception=Exception
            )
            for provider in APIProvider
        }
        
        # Semaphore for concurrent request limiting
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # Statistics tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'provider_stats': {provider: {'requests': 0, 'failures': 0} for provider in APIProvider}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=50, limit_per_host=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=60
    )
    async def _make_request(self, request: APIRequest) -> APIResponse:
        """Make a single API request with retries and circuit breaker"""
        if not self.session:
            raise RuntimeError("AsyncAPIManager must be used as async context manager")
        
        async with self.semaphore:
            # Apply rate limiting
            await self.rate_limiters[request.provider].acquire()
            
            # Use circuit breaker
            circuit_breaker = self.circuit_breakers[request.provider]
            
            try:
                response = await circuit_breaker.call(
                    self._execute_request, request
                )
                return response
            
            except Exception as e:
                logger.error(f"API request failed for {request.provider.value}: {e}")
                self._update_stats(request.provider, success=False)
                
                return APIResponse(
                    provider=request.provider,
                    data=None,
                    status_code=0,
                    response_time=0.0,
                    error=str(e),
                    success=False
                )
    
    async def _execute_request(self, request: APIRequest) -> APIResponse:
        """Execute the actual HTTP request"""
        start_time = time.time()
        
        async with self.session.request(
            method=request.method,
            url=request.endpoint,
            params=request.params,
            headers=request.headers or {},
            timeout=aiohttp.ClientTimeout(total=request.timeout)
        ) as response:
            
            response_time = time.time() - start_time
            data = await response.json()
            
            if response.status == 200:
                self._update_stats(request.provider, success=True, response_time=response_time)
                
                return APIResponse(
                    provider=request.provider,
                    data=data,
                    status_code=response.status,
                    response_time=response_time,
                    success=True
                )
            else:
                self._update_stats(request.provider, success=False, response_time=response_time)
                
                return APIResponse(
                    provider=request.provider,
                    data=data,
                    status_code=response.status,
                    response_time=response_time,
                    error=f"HTTP {response.status}",
                    success=False
                )
    
    async def execute_batch(self, requests: List[APIRequest]) -> List[APIResponse]:
        """Execute multiple API requests concurrently"""
        logger.info(f"Executing batch of {len(requests)} API requests")
        
        # Create tasks for concurrent execution
        tasks = [
            asyncio.create_task(self._make_request(request))
            for request in requests
        ]
        
        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Request {i} failed with exception: {response}")
                processed_responses.append(APIResponse(
                    provider=requests[i].provider,
                    data=None,
                    status_code=0,
                    response_time=0.0,
                    error=str(response),
                    success=False
                ))
            else:
                processed_responses.append(response)
        
        successful = sum(1 for r in processed_responses if r.success)
        logger.info(f"Batch completed: {successful}/{len(requests)} successful")
        
        return processed_responses
    
    async def search_papers_concurrent(
        self, 
        query: str, 
        providers: List[APIProvider] = None,
        max_results_per_provider: int = 50
    ) -> Dict[APIProvider, List[Paper]]:
        """Search for papers across multiple providers concurrently"""
        
        if providers is None:
            providers = list(APIProvider)
        
        # Create requests for each provider
        requests = []
        for provider in providers:
            request = self._create_search_request(
                provider, query, max_results_per_provider
            )
            if request:
                requests.append(request)
        
        # Execute all requests concurrently
        responses = await self.execute_batch(requests)
        
        # Process responses into papers
        results = {}
        for response in responses:
            if response.success:
                papers = self._parse_papers_from_response(response)
                results[response.provider] = papers
            else:
                logger.warning(
                    f"Search failed for {response.provider.value}: {response.error}"
                )
                results[response.provider] = []
        
        return results
    
    def _create_search_request(
        self, 
        provider: APIProvider, 
        query: str, 
        max_results: int
    ) -> Optional[APIRequest]:
        """Create API request for specific provider"""
        
        if provider == APIProvider.OPENALEX:
            return APIRequest(
                provider=provider,
                endpoint="https://api.openalex.org/works",
                params={
                    'search': query,
                    'per-page': min(max_results, 200),
                    'select': 'id,title,display_name,publication_date,primary_location,authorships,abstract_inverted_index,cited_by_count,doi'
                }
            )
        
        elif provider == APIProvider.CROSSREF:
            return APIRequest(
                provider=provider,
                endpoint="https://api.crossref.org/works",
                params={
                    'query': query,
                    'rows': min(max_results, 1000),
                    'select': 'DOI,title,author,abstract,published-print,container-title,is-referenced-by-count'
                }
            )
        
        elif provider == APIProvider.ARXIV:
            return APIRequest(
                provider=provider,
                endpoint="http://export.arxiv.org/api/query",
                params={
                    'search_query': f'all:{query}',
                    'start': 0,
                    'max_results': min(max_results, 1000),
                    'sortBy': 'relevance',
                    'sortOrder': 'descending'
                }
            )
        
        elif provider == APIProvider.SEMANTIC_SCHOLAR:
            return APIRequest(
                provider=provider,
                endpoint="https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    'query': query,
                    'limit': min(max_results, 100),
                    'fields': 'paperId,title,authors,abstract,venue,year,citationCount,url,isOpenAccess,openAccessPdf'
                }
            )
        
        return None
    
    def _parse_papers_from_response(self, response: APIResponse) -> List[Paper]:
        """Parse API response into Paper objects"""
        papers = []
        
        try:
            if response.provider == APIProvider.OPENALEX:
                papers = self._parse_openalex_papers(response.data)
            elif response.provider == APIProvider.CROSSREF:
                papers = self._parse_crossref_papers(response.data)
            elif response.provider == APIProvider.ARXIV:
                papers = self._parse_arxiv_papers(response.data)
            elif response.provider == APIProvider.SEMANTIC_SCHOLAR:
                papers = self._parse_semantic_scholar_papers(response.data)
        
        except Exception as e:
            logger.error(f"Failed to parse papers from {response.provider.value}: {e}")
        
        return papers
    
    def _parse_openalex_papers(self, data: Dict[str, Any]) -> List[Paper]:
        """Parse OpenAlex API response"""
        papers = []
        
        for item in data.get('results', []):
            try:
                paper = Paper(
                    id=item.get('id', '').replace('https://openalex.org/', ''),
                    title=item.get('display_name', ''),
                    authors=', '.join([
                        auth.get('author', {}).get('display_name', '')
                        for auth in item.get('authorships', [])
                    ]),
                    abstract=self._reconstruct_abstract(item.get('abstract_inverted_index')),
                    url=item.get('id', ''),
                    published_date=item.get('publication_date', ''),
                    venue=item.get('primary_location', {}).get('source', {}).get('display_name', ''),
                    citations=item.get('cited_by_count', 0),
                    doi=item.get('doi', ''),
                    created_at=time.strftime('%Y-%m-%d %H:%M:%S')
                )
                papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to parse OpenAlex paper: {e}")
        
        return papers
    
    def _parse_crossref_papers(self, data: Dict[str, Any]) -> List[Paper]:
        """Parse CrossRef API response"""
        papers = []
        
        for item in data.get('message', {}).get('items', []):
            try:
                authors = ', '.join([
                    f"{auth.get('given', '')} {auth.get('family', '')}"
                    for auth in item.get('author', [])
                ])
                
                paper = Paper(
                    id=item.get('DOI', ''),
                    title=' '.join(item.get('title', [''])),
                    authors=authors,
                    abstract=item.get('abstract', ''),
                    url=f"https://doi.org/{item.get('DOI', '')}",
                    published_date=self._extract_date(item.get('published-print')),
                    venue=' '.join(item.get('container-title', [''])),
                    citations=item.get('is-referenced-by-count', 0),
                    doi=item.get('DOI', ''),
                    created_at=time.strftime('%Y-%m-%d %H:%M:%S')
                )
                papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to parse CrossRef paper: {e}")
        
        return papers
    
    def _parse_semantic_scholar_papers(self, data: Dict[str, Any]) -> List[Paper]:
        """Parse Semantic Scholar API response"""
        papers = []
        
        for item in data.get('data', []):
            try:
                authors = ', '.join([
                    auth.get('name', '')
                    for auth in item.get('authors', [])
                ])
                
                paper = Paper(
                    id=item.get('paperId', ''),
                    title=item.get('title', ''),
                    authors=authors,
                    abstract=item.get('abstract', ''),
                    url=item.get('url', ''),
                    published_date=str(item.get('year', '')),
                    venue=item.get('venue', ''),
                    citations=item.get('citationCount', 0),
                    created_at=time.strftime('%Y-%m-%d %H:%M:%S')
                )
                papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to parse Semantic Scholar paper: {e}")
        
        return papers
    
    def _parse_arxiv_papers(self, data: str) -> List[Paper]:
        """Parse ArXiv XML response"""
        papers = []
        
        # ArXiv returns XML, would need XML parsing here
        # For now, return empty list
        logger.warning("ArXiv XML parsing not implemented in async version")
        
        return papers
    
    def _reconstruct_abstract(self, inverted_index: Optional[Dict[str, List[int]]]) -> str:
        """Reconstruct abstract from OpenAlex inverted index"""
        if not inverted_index:
            return ""
        
        try:
            # Create list of (position, word) pairs
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            
            # Sort by position and join words
            word_positions.sort(key=lambda x: x[0])
            return ' '.join([word for _, word in word_positions])
        
        except Exception:
            return ""
    
    def _extract_date(self, date_obj: Optional[Dict[str, Any]]) -> str:
        """Extract date string from CrossRef date object"""
        if not date_obj or 'date-parts' not in date_obj:
            return ""
        
        try:
            date_parts = date_obj['date-parts'][0]
            if len(date_parts) >= 3:
                return f"{date_parts[0]:04d}-{date_parts[1]:02d}-{date_parts[2]:02d}"
            elif len(date_parts) >= 1:
                return str(date_parts[0])
        except (IndexError, TypeError):
            pass
        
        return ""
    
    def _update_stats(
        self, 
        provider: APIProvider, 
        success: bool, 
        response_time: float = 0.0
    ):
        """Update statistics tracking"""
        self.stats['total_requests'] += 1
        self.stats['provider_stats'][provider]['requests'] += 1
        
        if success:
            self.stats['successful_requests'] += 1
            
            # Update average response time
            total_successful = self.stats['successful_requests']
            current_avg = self.stats['average_response_time']
            self.stats['average_response_time'] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
        else:
            self.stats['failed_requests'] += 1
            self.stats['provider_stats'][provider]['failures'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        stats = self.stats.copy()
        
        # Add success rate
        total = stats['total_requests']
        if total > 0:
            stats['success_rate'] = stats['successful_requests'] / total
        else:
            stats['success_rate'] = 0.0
        
        # Add provider success rates
        for provider, provider_stats in stats['provider_stats'].items():
            requests = provider_stats['requests']
            if requests > 0:
                provider_stats['success_rate'] = (
                    (requests - provider_stats['failures']) / requests
                )
            else:
                provider_stats['success_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset statistics tracking"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'provider_stats': {provider: {'requests': 0, 'failures': 0} for provider in APIProvider}
        }
