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
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Safely convert a database row to dictionary"""
        try:
            if hasattr(row, 'keys'):
                # sqlite_utils Row object or sqlite3.Row
                return {key: row[key] for key in row.keys()}
            elif isinstance(row, dict):
                return row
            elif isinstance(row, (list, tuple)):
                # Handle raw tuple/list rows - this shouldn't happen with sqlite_utils
                logger.warning("Received raw tuple/list row - this indicates a database issue")
                return {}
            else:
                logger.warning(f"Unknown row type: {type(row)}")
                return {}
        except Exception as e:
            logger.error(f"Error converting row to dict: {e}")
            return {}
    
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
            if row:
                row_dict = self._row_to_dict(row)
                return Paper.from_dict(row_dict)
            return None
        except Exception as e:
            logger.error(f"Error getting paper {paper_id}: {e}")
            return None
    
    def search_papers(self, query: str, limit: int = 50, sort_by: str = 'relevance') -> List[Paper]:
        """Search papers by title or abstract with sorting"""
        try:
            # Build ORDER BY clause based on sort_by parameter
            if sort_by == 'date':
                order_clause = "ORDER BY published_date DESC"
            elif sort_by == 'citations':
                order_clause = "ORDER BY citations DESC"
            else:  # relevance (default)
                order_clause = "ORDER BY citations DESC"  # Use citations as proxy for relevance
            
            sql = f"""
                SELECT * FROM papers 
                WHERE title LIKE ? OR abstract LIKE ?
                {order_clause}
                LIMIT ?
            """
            rows = self.db.execute(sql, [f"%{query}%", f"%{query}%", limit]).fetchall()
            
            papers = []
            for row in rows:
                try:
                    # Convert row to dict properly
                    row_dict = self._row_to_dict(row)
                    if row_dict:  # Only proceed if conversion was successful
                        paper = Paper.from_dict(row_dict)
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"Error converting row to paper: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []
    
    def get_all_papers(self) -> List[Paper]:
        """Get all papers"""
        try:
            papers = []
            for row in self.db['papers'].rows:
                try:
                    row_dict = self._row_to_dict(row)
                    if row_dict:
                        paper = Paper.from_dict(row_dict)
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"Error converting paper row: {e}")
                    continue
            return papers
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
            
            notes = []
            for row in rows:
                try:
                    row_dict = self._row_to_dict(row)
                    if row_dict:
                        note = ResearchNote(**row_dict)
                        notes.append(note)
                except Exception as e:
                    logger.warning(f"Error converting note row: {e}")
                    continue
            return notes
            
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
    
    def get_themes(self, min_frequency: int = 1, limit: Optional[int] = None) -> List[ResearchTheme]:
        """Get research themes with minimum frequency and optional limit"""
        try:
            sql = "SELECT * FROM research_themes WHERE frequency >= ? ORDER BY frequency DESC"
            params = [min_frequency]
            
            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)
            
            rows = self.db.execute(sql, params).fetchall()
            
            themes = []
            for row in rows:
                try:
                    row_dict = self._row_to_dict(row)
                    if row_dict:
                        theme = ResearchTheme(**row_dict)
                        themes.append(theme)
                except Exception as e:
                    logger.warning(f"Error creating theme from row: {e}")
                    continue
            
            return themes
            
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
            
            if row:
                row_dict = self._row_to_dict(row)
                if row_dict:
                    return Citation(**row_dict)
            return None
            
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
    
    def clear_corrupted_data(self):
        """Clear potentially corrupted data - use with caution"""
        try:
            # Check for and clean up malformed rows
            logger.info("Checking for corrupted data...")
            
            # Test each table for corruption
            tables = ['papers', 'research_notes', 'research_themes', 'citations']
            for table_name in tables:
                try:
                    rows = list(self.db[table_name].rows)
                    clean_rows = []
                    corrupted_count = 0
                    
                    for row in rows:
                        try:
                            # Try to convert each row
                            row_dict = self._row_to_dict(row)
                            if row_dict:
                                clean_rows.append(row_dict)
                            else:
                                corrupted_count += 1
                        except Exception:
                            corrupted_count += 1
                    
                    if corrupted_count > 0:
                        logger.warning(f"Found {corrupted_count} corrupted rows in {table_name}")
                        
                except Exception as e:
                    logger.error(f"Error checking table {table_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error during corruption check: {e}")

# Global database instance
db = DatabaseManager()