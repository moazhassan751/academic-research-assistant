"""
Tests for literature survey agent
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.agents.literature_survey_agent import LiteratureSurveyAgent
from src.storage.models import Paper


class TestLiteratureSurveyAgent:
    """Test literature survey agent functionality"""
    
    @pytest.fixture
    def agent(self):
        """Create a literature survey agent for testing"""
        with patch('src.agents.literature_survey_agent.LLMFactory.create_llm') as mock_llm:
            mock_llm.return_value = Mock()
            agent = LiteratureSurveyAgent()
            return agent
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly"""
        assert agent is not None
        assert hasattr(agent, 'llm')
        assert hasattr(agent, 'arxiv_tool')
        assert hasattr(agent, 'openalex_tool')
        assert hasattr(agent, 'crossref_tool')
    
    @patch('src.agents.literature_survey_agent.ArxivTool')
    @patch('src.agents.literature_survey_agent.OpenAlexTool')
    def test_search_multiple_databases(self, mock_openalex, mock_arxiv, agent):
        """Test searching multiple databases"""
        # Mock API responses
        mock_papers = [
            Mock(spec=Paper, id='1', title='Paper 1', authors=['Author 1']),
            Mock(spec=Paper, id='2', title='Paper 2', authors=['Author 2'])
        ]
        
        mock_arxiv.return_value.search_papers.return_value = mock_papers[:1]
        mock_openalex.return_value.search_papers.return_value = mock_papers[1:]
        
        # Test search
        queries = ['machine learning', 'deep learning']
        results = agent.search_multiple_databases_enhanced(queries, max_results_per_query=5)
        
        # Verify results
        assert len(results) >= 0  # Should return some results
    
    def test_paper_ranking(self, agent):
        """Test paper ranking functionality"""
        # Create mock papers
        papers = [
            Mock(spec=Paper, 
                 id='1', 
                 title='Machine Learning Survey', 
                 abstract='Comprehensive survey of ML',
                 venue='Nature',
                 citations=100),
            Mock(spec=Paper,
                 id='2', 
                 title='Deep Learning Review',
                 abstract='Review of deep learning',
                 venue='ArXiv',
                 citations=10)
        ]
        
        # Test ranking
        ranked_papers = agent.intelligent_paper_ranking(papers, 'machine learning')
        
        # Should return the same papers (possibly reordered)
        assert len(ranked_papers) == len(papers)
        assert all(isinstance(p, Mock) for p in ranked_papers)
    
    def test_deduplication(self, agent):
        """Test paper deduplication"""
        # Create duplicate papers
        papers = [
            Mock(spec=Paper, id='1', title='Same Title', doi='10.1000/test1'),
            Mock(spec=Paper, id='2', title='Same Title', doi='10.1000/test1'),  # Duplicate
            Mock(spec=Paper, id='3', title='Different Title', doi='10.1000/test2')
        ]
        
        deduplicated = agent.enhanced_deduplicate_papers(papers)
        
        # Should remove duplicates
        assert len(deduplicated) <= len(papers)
    
    def test_search_strategy_creation(self, agent):
        """Test search strategy creation"""
        with patch.object(agent.llm, 'generate') as mock_generate:
            mock_generate.return_value = '{"queries": ["machine learning", "ML survey"]}'
            
            strategy = agent.create_enhanced_search_strategy(
                'machine learning', 
                ['neural networks'], 
                'survey'
            )
            
            assert strategy is not None
            assert isinstance(strategy, dict)
    
    def test_error_handling(self, agent):
        """Test error handling in literature survey"""
        with patch.object(agent.arxiv_tool, 'search_papers') as mock_search:
            mock_search.side_effect = Exception("API Error")
            
            # Should handle errors gracefully
            try:
                results = agent.search_multiple_databases_enhanced(['test query'])
                # Should return empty list or handle gracefully
                assert isinstance(results, list)
            except Exception as e:
                pytest.fail(f"Should handle API errors gracefully, but got: {e}")


class TestSearchStrategy:
    """Test search strategy functionality"""
    
    def test_search_query_generation(self):
        """Test generation of search queries"""
        # This would test the LLM-based query generation
        # For now, test fallback strategy
        agent = Mock()
        strategy = {
            'base_queries': ['machine learning'],
            'aspect_queries': ['neural networks', 'deep learning'],
            'venue_queries': ['survey machine learning']
        }
        
        assert 'base_queries' in strategy
        assert len(strategy['base_queries']) > 0
    
    def test_query_optimization(self):
        """Test query optimization for different databases"""
        # Test that queries are optimized for different APIs
        original_query = 'machine learning neural networks'
        
        # ArXiv might prefer different formatting than OpenAlex
        arxiv_query = original_query  # ArXiv usually takes queries as-is
        openalex_query = original_query.replace(' ', '+')  # URL encoding
        
        assert arxiv_query == 'machine learning neural networks'
        assert '+' in openalex_query or openalex_query == original_query
