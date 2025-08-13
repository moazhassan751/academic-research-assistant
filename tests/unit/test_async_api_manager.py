"""
Tests for async API processing functionality
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch
from src.utils.async_api_manager import (
    AsyncAPIManager, 
    APIProvider, 
    APIRequest, 
    APIResponse,
    RateLimiter,
    CircuitBreaker
)
from src.storage.models import Paper


class TestRateLimiter:
    """Test rate limiter functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting functionality"""
        limiter = RateLimiter(calls_per_second=2.0)  # Allow 2 calls per second
        
        start_time = asyncio.get_event_loop().time()
        
        # Make 3 calls - should take at least 1 second total
        for _ in range(3):
            await limiter.acquire()
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        # Should take at least 1 second (1/2 * 2 additional calls)
        assert elapsed >= 1.0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent(self):
        """Test rate limiter with concurrent calls"""
        limiter = RateLimiter(calls_per_second=1.0)
        
        async def make_call():
            await limiter.acquire()
            return asyncio.get_event_loop().time()
        
        # Make multiple concurrent calls
        start_time = asyncio.get_event_loop().time()
        times = await asyncio.gather(*[make_call() for _ in range(3)])
        
        # Calls should be spaced out by at least 1 second
        for i in range(1, len(times)):
            time_diff = times[i] - times[i-1]
            assert time_diff >= 0.9  # Allow some tolerance for timing


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self):
        """Test circuit breaker with successful calls"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        
        async def success_func():
            return "success"
        
        # Successful call should work
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == 'closed'
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure(self):
        """Test circuit breaker with failures"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        async def failing_func():
            raise Exception("Test failure")
        
        # First failure
        with pytest.raises(Exception):
            await breaker.call(failing_func)
        
        assert breaker.failure_count == 1
        assert breaker.state == 'closed'
        
        # Second failure should open circuit
        with pytest.raises(Exception):
            await breaker.call(failing_func)
        
        assert breaker.failure_count == 2
        assert breaker.state == 'open'
        
        # Third call should fail immediately due to open circuit
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.call(failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery"""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        async def failing_func():
            raise Exception("Test failure")
        
        async def success_func():
            return "recovered"
        
        # Trigger failure to open circuit
        with pytest.raises(Exception):
            await breaker.call(failing_func)
        
        assert breaker.state == 'open'
        
        # Wait for recovery timeout
        await asyncio.sleep(0.2)
        
        # Should now allow calls and reset on success
        result = await breaker.call(success_func)
        assert result == "recovered"
        assert breaker.state == 'closed'
        assert breaker.failure_count == 0


class TestAsyncAPIManager:
    """Test async API manager"""
    
    @pytest.fixture
    async def api_manager(self):
        """Create API manager for testing"""
        async with AsyncAPIManager(max_concurrent_requests=5) as manager:
            yield manager
    
    @pytest.fixture
    def mock_response_data(self):
        """Mock API response data"""
        return {
            'openalex': {
                'results': [
                    {
                        'id': 'https://openalex.org/W123456',
                        'display_name': 'Test Paper',
                        'authorships': [
                            {'author': {'display_name': 'John Doe'}}
                        ],
                        'abstract_inverted_index': {'test': [0], 'abstract': [1]},
                        'publication_date': '2023-01-01',
                        'primary_location': {
                            'source': {'display_name': 'Nature'}
                        },
                        'cited_by_count': 10,
                        'doi': '10.1000/test'
                    }
                ]
            },
            'crossref': {
                'message': {
                    'items': [
                        {
                            'DOI': '10.1000/test2',
                            'title': ['CrossRef Test Paper'],
                            'author': [
                                {'given': 'Jane', 'family': 'Smith'}
                            ],
                            'abstract': 'Test abstract',
                            'published-print': {
                                'date-parts': [[2023, 2, 15]]
                            },
                            'container-title': ['Science'],
                            'is-referenced-by-count': 5
                        }
                    ]
                }
            },
            'semantic_scholar': {
                'data': [
                    {
                        'paperId': 'SS123456',
                        'title': 'Semantic Scholar Test',
                        'authors': [{'name': 'Alice Johnson'}],
                        'abstract': 'SS test abstract',
                        'url': 'https://semanticscholar.org/paper/SS123456',
                        'year': 2023,
                        'venue': 'ICML',
                        'citationCount': 8
                    }
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_api_manager_initialization(self, api_manager):
        """Test API manager initialization"""
        assert api_manager.max_concurrent_requests == 5
        assert len(api_manager.rate_limiters) == 4  # 4 providers
        assert len(api_manager.circuit_breakers) == 4
        assert api_manager.session is not None
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, api_manager, mock_response_data):
        """Test successful API request"""
        request = APIRequest(
            provider=APIProvider.OPENALEX,
            endpoint="https://api.openalex.org/works",
            params={'search': 'test'}
        )
        
        # Mock the HTTP response
        with patch.object(api_manager.session, 'request') as mock_request:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json.return_value = mock_response_data['openalex']
            mock_request.return_value.__aenter__.return_value = mock_resp
            
            response = await api_manager._make_request(request)
            
            assert response.success
            assert response.status_code == 200
            assert response.provider == APIProvider.OPENALEX
            assert response.data == mock_response_data['openalex']
    
    @pytest.mark.asyncio
    async def test_make_request_failure(self, api_manager):
        """Test failed API request"""
        request = APIRequest(
            provider=APIProvider.OPENALEX,
            endpoint="https://api.openalex.org/works",
            params={'search': 'test'}
        )
        
        # Mock the HTTP response failure
        with patch.object(api_manager.session, 'request') as mock_request:
            mock_resp = AsyncMock()
            mock_resp.status = 500
            mock_resp.json.return_value = {'error': 'Server error'}
            mock_request.return_value.__aenter__.return_value = mock_resp
            
            response = await api_manager._make_request(request)
            
            assert not response.success
            assert response.status_code == 500
            assert 'HTTP 500' in response.error
    
    @pytest.mark.asyncio
    async def test_execute_batch(self, api_manager, mock_response_data):
        """Test batch request execution"""
        requests = [
            APIRequest(
                provider=APIProvider.OPENALEX,
                endpoint="https://api.openalex.org/works",
                params={'search': 'test1'}
            ),
            APIRequest(
                provider=APIProvider.CROSSREF,
                endpoint="https://api.crossref.org/works",
                params={'query': 'test2'}
            )
        ]
        
        # Mock successful responses
        with patch.object(api_manager, '_make_request') as mock_make_request:
            mock_make_request.side_effect = [
                APIResponse(
                    provider=APIProvider.OPENALEX,
                    data=mock_response_data['openalex'],
                    status_code=200,
                    response_time=0.5,
                    success=True
                ),
                APIResponse(
                    provider=APIProvider.CROSSREF,
                    data=mock_response_data['crossref'],
                    status_code=200,
                    response_time=0.7,
                    success=True
                )
            ]
            
            responses = await api_manager.execute_batch(requests)
            
            assert len(responses) == 2
            assert all(r.success for r in responses)
            assert responses[0].provider == APIProvider.OPENALEX
            assert responses[1].provider == APIProvider.CROSSREF
    
    @pytest.mark.asyncio
    async def test_search_papers_concurrent(self, api_manager, mock_response_data):
        """Test concurrent paper search across providers"""
        # Mock the request creation and execution
        with patch.object(api_manager, '_create_search_request') as mock_create, \
             patch.object(api_manager, 'execute_batch') as mock_batch:
            
            # Mock request creation
            mock_create.side_effect = [
                APIRequest(
                    provider=APIProvider.OPENALEX,
                    endpoint="https://api.openalex.org/works",
                    params={'search': 'machine learning'}
                ),
                APIRequest(
                    provider=APIProvider.SEMANTIC_SCHOLAR,
                    endpoint="https://api.semanticscholar.org/graph/v1/paper/search",
                    params={'query': 'machine learning'}
                )
            ]
            
            # Mock batch execution
            mock_batch.return_value = [
                APIResponse(
                    provider=APIProvider.OPENALEX,
                    data=mock_response_data['openalex'],
                    status_code=200,
                    response_time=0.5,
                    success=True
                ),
                APIResponse(
                    provider=APIProvider.SEMANTIC_SCHOLAR,
                    data=mock_response_data['semantic_scholar'],
                    status_code=200,
                    response_time=0.8,
                    success=True
                )
            ]
            
            results = await api_manager.search_papers_concurrent(
                query='machine learning',
                providers=[APIProvider.OPENALEX, APIProvider.SEMANTIC_SCHOLAR]
            )
            
            assert len(results) == 2
            assert APIProvider.OPENALEX in results
            assert APIProvider.SEMANTIC_SCHOLAR in results
            assert len(results[APIProvider.OPENALEX]) == 1  # One paper from OpenAlex
            assert len(results[APIProvider.SEMANTIC_SCHOLAR]) == 1  # One paper from SS
    
    def test_parse_openalex_papers(self, mock_response_data):
        """Test OpenAlex paper parsing"""
        manager = AsyncAPIManager()
        papers = manager._parse_openalex_papers(mock_response_data['openalex'])
        
        assert len(papers) == 1
        paper = papers[0]
        assert paper.title == 'Test Paper'
        assert paper.authors == 'John Doe'
        assert paper.abstract == 'test abstract'
        assert paper.venue == 'Nature'
        assert paper.citations == 10
        assert paper.doi == '10.1000/test'
    
    def test_parse_crossref_papers(self, mock_response_data):
        """Test CrossRef paper parsing"""
        manager = AsyncAPIManager()
        papers = manager._parse_crossref_papers(mock_response_data['crossref'])
        
        assert len(papers) == 1
        paper = papers[0]
        assert paper.title == 'CrossRef Test Paper'
        assert paper.authors == 'Jane Smith'
        assert paper.abstract == 'Test abstract'
        assert paper.venue == 'Science'
        assert paper.citations == 5
        assert paper.doi == '10.1000/test2'
    
    def test_parse_semantic_scholar_papers(self, mock_response_data):
        """Test Semantic Scholar paper parsing"""
        manager = AsyncAPIManager()
        papers = manager._parse_semantic_scholar_papers(mock_response_data['semantic_scholar'])
        
        assert len(papers) == 1
        paper = papers[0]
        assert paper.title == 'Semantic Scholar Test'
        assert paper.authors == 'Alice Johnson'
        assert paper.abstract == 'SS test abstract'
        assert paper.venue == 'ICML'
        assert paper.citations == 8
    
    def test_reconstruct_abstract(self):
        """Test abstract reconstruction from inverted index"""
        manager = AsyncAPIManager()
        
        inverted_index = {
            'This': [0],
            'is': [1],
            'a': [2],
            'test': [3],
            'abstract': [4]
        }
        
        abstract = manager._reconstruct_abstract(inverted_index)
        assert abstract == 'This is a test abstract'
    
    def test_extract_date(self):
        """Test date extraction from CrossRef format"""
        manager = AsyncAPIManager()
        
        # Full date
        date_obj = {'date-parts': [[2023, 12, 15]]}
        result = manager._extract_date(date_obj)
        assert result == '2023-12-15'
        
        # Year only
        date_obj = {'date-parts': [[2023]]}
        result = manager._extract_date(date_obj)
        assert result == '2023'
        
        # Invalid date
        result = manager._extract_date(None)
        assert result == ''
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self, api_manager):
        """Test API statistics tracking"""
        # Initial stats should be empty
        stats = api_manager.get_statistics()
        assert stats['total_requests'] == 0
        assert stats['successful_requests'] == 0
        assert stats['success_rate'] == 0.0
        
        # Update stats
        api_manager._update_stats(APIProvider.OPENALEX, success=True, response_time=0.5)
        api_manager._update_stats(APIProvider.OPENALEX, success=False)
        
        stats = api_manager.get_statistics()
        assert stats['total_requests'] == 2
        assert stats['successful_requests'] == 1
        assert stats['failed_requests'] == 1
        assert stats['success_rate'] == 0.5
        assert stats['average_response_time'] == 0.5
        
        # Provider-specific stats
        openalex_stats = stats['provider_stats'][APIProvider.OPENALEX]
        assert openalex_stats['requests'] == 2
        assert openalex_stats['failures'] == 1
        assert openalex_stats['success_rate'] == 0.5
    
    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self, api_manager):
        """Test concurrent request limiting with semaphore"""
        # This test verifies that the semaphore limits concurrent requests
        # We'll mock slow requests to test this
        
        request = APIRequest(
            provider=APIProvider.OPENALEX,
            endpoint="https://api.openalex.org/works",
            params={'search': 'test'}
        )
        
        async def slow_request():
            await asyncio.sleep(0.1)  # Simulate slow request
            return APIResponse(
                provider=APIProvider.OPENALEX,
                data={},
                status_code=200,
                response_time=0.1,
                success=True
            )
        
        # Mock the _make_request to be slow
        with patch.object(api_manager, '_make_request', side_effect=slow_request):
            # Try to execute more requests than the semaphore limit
            start_time = asyncio.get_event_loop().time()
            
            tasks = [api_manager._make_request(request) for _ in range(10)]
            await asyncio.gather(*tasks)
            
            end_time = asyncio.get_event_loop().time()
            elapsed = end_time - start_time
            
            # With a limit of 5 concurrent requests and 10 total requests
            # taking 0.1s each, we should see at least 2 batches
            # So minimum time should be around 0.2s
            assert elapsed >= 0.15  # Allow some tolerance
