"""
Tests for input validators
"""

import pytest
from src.utils.validators import (
    validate_research_query,
    validate_export_formats,
    validate_paper_data,
    sanitize_filename,
    validate_search_query,
    ResearchQueryValidator
)


class TestResearchQueryValidator:
    """Test research query validation"""
    
    def test_valid_query(self):
        """Test valid research query"""
        data = {
            'topic': 'machine learning',
            'max_papers': 50,
            'paper_type': 'survey',
            'aspects': ['deep learning', 'neural networks']
        }
        result = validate_research_query(data)
        assert result.topic == 'machine learning'
        assert result.max_papers == 50
        assert result.paper_type == 'survey'
        assert len(result.aspects) == 2
    
    def test_empty_topic_fails(self):
        """Test that empty topic fails validation"""
        data = {'topic': '', 'max_papers': 10}
        with pytest.raises(ValueError, match="Research topic cannot be empty"):
            validate_research_query(data)
    
    def test_short_topic_fails(self):
        """Test that very short topic fails validation"""
        data = {'topic': 'AI', 'max_papers': 10}
        with pytest.raises(ValueError, match="Research topic must be at least 3 characters"):
            validate_research_query(data)
    
    def test_long_topic_fails(self):
        """Test that very long topic fails validation"""
        data = {'topic': 'x' * 201, 'max_papers': 10}
        with pytest.raises(ValueError, match="Research topic must be less than 200 characters"):
            validate_research_query(data)
    
    def test_invalid_max_papers(self):
        """Test invalid max_papers values"""
        # Too low
        data = {'topic': 'machine learning', 'max_papers': 0}
        with pytest.raises(ValueError, match="max_papers must be at least 1"):
            validate_research_query(data)
        
        # Too high
        data = {'topic': 'machine learning', 'max_papers': 1000}
        with pytest.raises(ValueError, match="max_papers cannot exceed 500"):
            validate_research_query(data)
    
    def test_invalid_paper_type(self):
        """Test invalid paper type"""
        data = {'topic': 'machine learning', 'paper_type': 'invalid'}
        with pytest.raises(ValueError, match="paper_type must be one of"):
            validate_research_query(data)
    
    def test_too_many_aspects(self):
        """Test too many aspects"""
        data = {
            'topic': 'machine learning',
            'aspects': [f'aspect{i}' for i in range(15)]
        }
        with pytest.raises(ValueError, match="Cannot specify more than 10 aspects"):
            validate_research_query(data)
    
    def test_malicious_input_sanitization(self):
        """Test that malicious input is sanitized"""
        data = {
            'topic': 'machine learning<script>alert("xss")</script>',
            'aspects': ['deep learning"; DROP TABLE papers; --']
        }
        result = validate_research_query(data)
        assert '<script>' not in result.topic
        assert 'DROP TABLE' not in result.aspects[0]


class TestExportFormatValidator:
    """Test export format validation"""
    
    def test_valid_formats(self):
        """Test valid export formats"""
        data = {'formats': ['pdf', 'docx', 'markdown']}
        result = validate_export_formats(data)
        assert len(result.formats) == 3
        assert 'pdf' in result.formats
    
    def test_invalid_format(self):
        """Test invalid export format"""
        data = {'formats': ['pdf', 'invalid_format']}
        with pytest.raises(ValueError, match="Invalid format"):
            validate_export_formats(data)
    
    def test_empty_formats(self):
        """Test empty formats list"""
        data = {'formats': []}
        with pytest.raises(ValueError, match="At least one export format must be specified"):
            validate_export_formats(data)
    
    def test_duplicate_formats_removed(self):
        """Test that duplicate formats are removed"""
        data = {'formats': ['pdf', 'PDF', 'pdf', 'docx']}
        result = validate_export_formats(data)
        assert len(result.formats) == 2
        assert result.formats.count('pdf') == 1


class TestPaperValidator:
    """Test paper data validation"""
    
    def test_valid_paper(self, sample_paper):
        """Test valid paper data"""
        result = validate_paper_data(sample_paper)
        assert result.title == sample_paper['title']
        assert len(result.authors) == 2
    
    def test_empty_title_fails(self, sample_paper):
        """Test that empty title fails validation"""
        sample_paper['title'] = ''
        with pytest.raises(ValueError, match="Paper title cannot be empty"):
            validate_paper_data(sample_paper)
    
    def test_no_authors_fails(self, sample_paper):
        """Test that no authors fails validation"""
        sample_paper['authors'] = []
        with pytest.raises(ValueError, match="At least one author must be specified"):
            validate_paper_data(sample_paper)
    
    def test_invalid_url_fails(self, sample_paper):
        """Test that invalid URL fails validation"""
        sample_paper['url'] = 'not-a-valid-url'
        with pytest.raises(ValueError, match="Invalid URL format"):
            validate_paper_data(sample_paper)
    
    def test_invalid_doi_fails(self, sample_paper):
        """Test that invalid DOI fails validation"""
        sample_paper['doi'] = 'not-a-valid-doi'
        with pytest.raises(ValueError, match="Invalid DOI format"):
            validate_paper_data(sample_paper)


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test dangerous characters
        result = sanitize_filename('file<name>with:bad"chars*.txt')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '*' not in result
    
    def test_validate_search_query(self):
        """Test search query validation"""
        # Valid query
        result = validate_search_query('machine learning')
        assert result == 'machine learning'
        
        # Empty query
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            validate_search_query('')
        
        # Too short
        with pytest.raises(ValueError, match="Search query must be at least 2 characters"):
            validate_search_query('a')
        
        # Too long
        with pytest.raises(ValueError, match="Search query too long"):
            validate_search_query('x' * 501)
