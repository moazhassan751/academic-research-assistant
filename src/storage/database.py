import sqlite3
import sqlite_utils
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models import Paper, ResearchNote, ResearchTheme, Citation
from ..utils.config import config
from ..utils.logging import logger

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.get('storage.database_path', 'data/research.db')
        self.db = sqlite_utils.Database(self.db_path)
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize database tables"""
        # Papers table
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT,
                abstract TEXT,
                url TEXT,
                published_date TEXT,
                venue TEXT,
                citations INTEGER DEFAULT 0,
                pdf_path TEXT,
                full_text TEXT,
                keywords TEXT,
                doi TEXT,
                arxiv_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS research_notes (
                id TEXT PRIMARY KEY,
                paper_id TEXT,
                content TEXT NOT NULL,
                note_type TEXT,
                confidence REAL DEFAULT 0.0,
                page_number INTEGER,
                created_at TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            );
            
            CREATE TABLE IF NOT EXISTS research_themes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                papers TEXT,
                frequency INTEGER DEFAULT 0,
                confidence REAL DEFAULT 0.0,
                related_themes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS citations (
                id TEXT PRIMARY KEY,
                paper_id TEXT,
                citation_key TEXT,
                apa_format TEXT,
                mla_format TEXT,
                bibtex TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title);
            CREATE INDEX IF NOT EXISTS idx_notes_paper_id ON research_notes(paper_id);
            CREATE INDEX IF NOT EXISTS idx_themes_frequency ON research_themes(frequency);
        """)
        
        logger.info(f"Database initialized at: {self.db_path}")
    
    # Paper operations
    def save_paper(self, paper: Paper) -> bool:
        """Save a paper to the database"""
        try:
            self.db['papers'].insert(paper.to_dict(), replace=True)
            return True
        except Exception as e:
            logger.error(f"Error saving paper {paper.id}: {e}")
            return False
    
    def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by ID"""
        try:
            row = self.db['papers'].get(paper_id)
            return Paper.from_dict(dict(row)) if row else None
        except Exception as e:
            logger.error(f"Error getting paper {paper_id}: {e}")
            return None
    
    def search_papers(self, query: str, limit: int = 50) -> List[Paper]:
        """Search papers by title or abstract"""
        try:
            sql = """
                SELECT * FROM papers 
                WHERE title LIKE ? OR abstract LIKE ?
                ORDER BY citations DESC
                LIMIT ?
            """
            rows = self.db.execute(sql, [f"%{query}%", f"%{query}%", limit]).fetchall()
            return [Paper.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []
    
    def get_all_papers(self) -> List[Paper]:
        """Get all papers"""
        try:
            rows = self.db['papers'].rows
            return [Paper.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all papers: {e}")
            return []
    
    # Note operations
    def save_note(self, note: ResearchNote) -> bool:
        """Save a research note"""
        try:
            self.db['research_notes'].insert(note.to_dict(), replace=True)
            return True
        except Exception as e:
            logger.error(f"Error saving note {note.id}: {e}")
            return False
    
    def get_notes_for_paper(self, paper_id: str) -> List[ResearchNote]:
        """Get all notes for a specific paper"""
        try:
            rows = self.db.execute(
                "SELECT * FROM research_notes WHERE paper_id = ?", 
                [paper_id]
            ).fetchall()
            return [ResearchNote(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting notes for paper {paper_id}: {e}")
            return []
    
    # Theme operations
    def save_theme(self, theme: ResearchTheme) -> bool:
        """Save a research theme"""
        try:
            self.db['research_themes'].insert(theme.to_dict(), replace=True)
            return True
        except Exception as e:
            logger.error(f"Error saving theme {theme.id}: {e}")
            return False
    
    def get_themes(self, min_frequency: int = 1) -> List[ResearchTheme]:
        """Get research themes with minimum frequency"""
        try:
            rows = self.db.execute(
                "SELECT * FROM research_themes WHERE frequency >= ? ORDER BY frequency DESC",
                [min_frequency]
            ).fetchall()
            return [ResearchTheme(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting themes: {e}")
            return []
    
    # Citation operations
    def save_citation(self, citation: Citation) -> bool:
        """Save a citation"""
        try:
            self.db['citations'].insert(citation.to_dict(), replace=True)
            return True
        except Exception as e:
            logger.error(f"Error saving citation {citation.id}: {e}")
            return False
    
    def get_citation(self, paper_id: str) -> Optional[Citation]:
        """Get citation for a paper"""
        try:
            row = self.db.execute(
                "SELECT * FROM citations WHERE paper_id = ?", 
                [paper_id]
            ).fetchone()
            return Citation(**dict(row)) if row else None
        except Exception as e:
            logger.error(f"Error getting citation for paper {paper_id}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        try:
            return {
                'papers': self.db['papers'].count,
                'notes': self.db['research_notes'].count,
                'themes': self.db['research_themes'].count,
                'citations': self.db['citations'].count
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

# Global database instance
db = DatabaseManager()