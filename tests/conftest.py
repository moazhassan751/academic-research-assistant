"""
Unit tests for Academic Research Assistant
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# Test configuration
@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'llm': {
            'provider': 'gemini',
            'model': 'gemini-2.5-flash',
            'temperature': 0.1,
            'max_tokens': 4096
        },
        'apis': {
            'openalex': {'base_url': 'https://api.openalex.org'},
            'crossref': {'base_url': 'https://api.crossref.org'},
            'arxiv': {'base_url': 'http://export.arxiv.org/api/query'}
        }
    }

@pytest.fixture
def sample_paper():
    """Sample paper data for testing"""
    return {
        'id': 'test-paper-123',
        'title': 'A Survey of Machine Learning Techniques',
        'authors': ['John Doe', 'Jane Smith'],
        'abstract': 'This paper provides a comprehensive survey of machine learning techniques...',
        'url': 'https://example.com/paper.pdf',
        'published_date': datetime(2023, 1, 15),
        'venue': 'Journal of AI Research',
        'citations': 42,
        'doi': '10.1000/test.doi'
    }

# Mark all tests as asyncio
pytestmark = pytest.mark.asyncio
