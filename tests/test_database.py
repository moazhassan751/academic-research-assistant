"""
Tests for database functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from src.storage.database import DatabaseManager
from src.storage.models import Paper, ResearchNote, ResearchTheme, Citation


class TestDatabaseManager:
    """Test database manager functionality"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        yield db
        
        # Properly close database connections before cleanup
        try:
            db.close()
        except AttributeError:
            pass  # DatabaseManager might not have a close method
        
        # Cleanup with retry for Windows file locking
        import time
        for attempt in range(3):
            try:
                if os.path.exists(db_path):
                    os.unlink(db_path)
                break
            except PermissionError:
                time.sleep(0.1)  # Brief delay before retry
    
    @pytest.fixture
    def sample_paper(self):
        """Create a sample paper for testing"""
        return Paper(
            id='test-paper-1',
            title='Test Paper Title',
            authors=['John Doe', 'Jane Smith'],
            abstract='This is a test paper abstract.',
            url='https://example.com/paper.pdf',
            published_date=datetime(2023, 1, 15),
            venue='Test Journal',
            citations=10,
            doi='10.1000/test.1'
        )
    
    def test_database_initialization(self, temp_db):
        """Test database initialization"""
        assert temp_db is not None
        assert os.path.exists(temp_db.db_path)
    
    def test_save_and_retrieve_paper(self, temp_db, sample_paper):
        """Test saving and retrieving papers"""
        # Save paper
        success = temp_db.save_paper(sample_paper)
        assert success
        
        # Retrieve paper
        retrieved = temp_db.get_paper(sample_paper.id)
        assert retrieved is not None
        assert retrieved.id == sample_paper.id
        assert retrieved.title == sample_paper.title
        assert len(retrieved.authors) == len(sample_paper.authors)
    
    def test_search_papers(self, temp_db, sample_paper):
        """Test paper search functionality"""
        # Save paper
        temp_db.save_paper(sample_paper)
        
        # Search by title
        results = temp_db.search_papers('Test Paper', limit=10)
        assert len(results) > 0
        assert any(p.id == sample_paper.id for p in results)
        
        # Search by author
        results = temp_db.search_papers('John Doe', limit=10)
        assert len(results) > 0
    
    def test_save_research_note(self, temp_db, sample_paper):
        """Test saving research notes"""
        # First save the paper
        temp_db.save_paper(sample_paper)
        
        # Create and save note
        note = ResearchNote(
            id='test-note-1',
            paper_id=sample_paper.id,
            content='This is a test research note.',
            note_type='key_finding',
            confidence=0.8
        )
        
        success = temp_db.save_note(note)
        assert success
        
        # Retrieve notes for paper
        notes = temp_db.get_notes_for_paper(sample_paper.id)
        assert len(notes) > 0
        assert notes[0].content == note.content
    
    def test_save_research_theme(self, temp_db):
        """Test saving research themes"""
        theme = ResearchTheme(
            id='test-theme-1',
            title='Test Theme',
            description='This is a test research theme.',
            papers=['paper1', 'paper2'],
            frequency=2,
            confidence=0.7
        )
        
        success = temp_db.save_theme(theme)
        assert success
        
        # Retrieve themes
        themes = temp_db.get_themes(min_frequency=1)
        assert len(themes) > 0
        assert themes[0].title == theme.title
    
    def test_save_citation(self, temp_db, sample_paper):
        """Test saving citations"""
        # First save the paper
        temp_db.save_paper(sample_paper)
        
        citation = Citation(
            id='test-citation-1',
            paper_id=sample_paper.id,
            citation_key='doe2023test',
            apa_format='Doe, J., & Smith, J. (2023). Test Paper Title.',
            mla_format='Doe, John, and Jane Smith. "Test Paper Title."',
            bibtex='@article{doe2023test, title={Test Paper Title}, author={Doe, John and Smith, Jane}}'
        )
        
        success = temp_db.save_citation(citation)
        assert success
        
        # Retrieve citation
        retrieved = temp_db.get_citation(sample_paper.id)
        assert retrieved is not None
        assert retrieved.citation_key == citation.citation_key
    
    def test_get_stats(self, temp_db, sample_paper):
        """Test database statistics"""
        # Add some data
        temp_db.save_paper(sample_paper)
        
        note = ResearchNote(
            id='test-note-1',
            paper_id=sample_paper.id,
            content='Test note',
            note_type='key_finding'
        )
        temp_db.save_note(note)
        
        # Get stats
        stats = temp_db.get_stats()
        assert 'papers' in stats
        assert 'notes' in stats
        assert stats['papers'] >= 1
        assert stats['notes'] >= 1
    
    def test_duplicate_paper_handling(self, temp_db, sample_paper):
        """Test handling of duplicate papers"""
        # Save paper twice
        success1 = temp_db.save_paper(sample_paper)
        success2 = temp_db.save_paper(sample_paper)
        
        assert success1
        # Second save might succeed (update) or fail (duplicate prevention)
        # Both are acceptable behaviors
        
        # Should still have only one paper
        all_papers = temp_db.get_all_papers()
        paper_ids = [p.id for p in all_papers]
        assert paper_ids.count(sample_paper.id) == 1
    
    def test_thread_safety(self, temp_db):
        """Test thread safety of database operations"""
        import threading
        import time
        
        results = []
        errors = []
        
        def save_papers(start_id):
            try:
                for i in range(5):
                    paper = Paper(
                        id=f'thread-paper-{start_id}-{i}',
                        title=f'Thread Paper {start_id} - {i}',
                        authors=['Thread Author'],
                        abstract='Thread test abstract',
                        url='https://example.com'
                    )
                    success = temp_db.save_paper(paper)
                    results.append(success)
                    time.sleep(0.01)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=save_papers, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert all(results), "Some saves failed"
        
        # Check that all papers were saved
        all_papers = temp_db.get_all_papers()
        assert len(all_papers) == 15  # 3 threads * 5 papers each
