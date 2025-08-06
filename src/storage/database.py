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
        # Keep track of column names for each table - initialize BEFORE _initialize_tables()
        self._column_cache = {}
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
        
        # Cache column names for each table
        self._cache_column_names()
        logger.info(f"Database initialized at: {self.db_path}")
    
    def _cache_column_names(self):
        """Cache column names for each table to handle raw tuple/list rows"""
        tables = ['papers', 'research_notes', 'research_themes', 'citations']
        for table_name in tables:
            try:
                # Get column information
                cursor = self.db.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]  # Column names are in index 1
                self._column_cache[table_name] = columns
                logger.debug(f"Cached columns for {table_name}: {columns}")
            except Exception as e:
                logger.error(f"Error caching columns for {table_name}: {e}")
                self._column_cache[table_name] = []
    
    def _row_to_dict(self, row, table_name: str = None) -> Dict[str, Any]:
        """Safely convert a database row to dictionary"""
        try:
            if hasattr(row, 'keys') and hasattr(row, '__getitem__'):
                # sqlite_utils Row object or sqlite3.Row
                return {key: row[key] for key in row.keys()}
            elif isinstance(row, dict):
                return row
            elif isinstance(row, (list, tuple)) and table_name:
                # Handle raw tuple/list rows using cached column names
                columns = self._column_cache.get(table_name, [])
                if len(columns) == len(row):
                    result = dict(zip(columns, row))
                    logger.debug(f"Converted raw {type(row).__name__} to dict for {table_name}")
                    return result
                else:
                    logger.warning(f"Column count mismatch for {table_name}: expected {len(columns)}, got {len(row)}")
                    return {}
            elif isinstance(row, (list, tuple)):
                # Raw tuple/list without table context - can't convert safely
                logger.warning("Received raw tuple/list row without table context - cannot convert")
                return {}
            else:
                logger.warning(f"Unknown row type: {type(row)}")
                return {}
        except Exception as e:
            logger.error(f"Error converting row to dict: {e}")
            return {}
    
    def _safe_create_paper(self, row_dict: Dict[str, Any]) -> Optional[Paper]:
        """Safely create Paper object from database row with enhanced error handling"""
        try:
            if not row_dict:
                return None
                
            # Ensure all required fields are present with defaults
            safe_dict = {
                'id': str(row_dict.get('id', '')),
                'title': str(row_dict.get('title', 'Untitled')),
                'authors': row_dict.get('authors', []),
                'abstract': str(row_dict.get('abstract', '')),
                'url': str(row_dict.get('url', '')),
                'published_date': row_dict.get('published_date'),
                'venue': row_dict.get('venue'),
                'citations': int(row_dict.get('citations', 0)),
                'pdf_path': row_dict.get('pdf_path'),
                'full_text': row_dict.get('full_text'),
                'keywords': row_dict.get('keywords', []),
                'doi': row_dict.get('doi'),
                'arxiv_id': row_dict.get('arxiv_id'),
                'created_at': row_dict.get('created_at')  # This field now exists in Paper model
            }
            
            # Skip papers with empty or invalid IDs
            if not safe_dict['id'] or safe_dict['id'] == 'None':
                logger.warning("Skipping paper with invalid ID")
                return None
                
            return Paper.from_dict(safe_dict)
            
        except Exception as e:
            logger.error(f"Error creating Paper object: {e}")
            logger.debug(f"Problematic row_dict: {row_dict}")
            return None
    
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
            # Use sqlite_utils table interface
            try:
                row = self.db['papers'].get(paper_id)
                if row:
                    row_dict = self._row_to_dict(row, 'papers')
                    return self._safe_create_paper(row_dict)
            except sqlite_utils.db.NotFoundError:
                return None
                
        except Exception as e:
            logger.error(f"Error getting paper {paper_id}: {e}")
            return None
    
    def search_papers(self, query: str, limit: int = 50, sort_by: str = 'relevance') -> List[Paper]:
        """Search papers by title or abstract with sorting and enhanced error handling"""
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
            
            # Use raw SQL execution to get consistent results
            cursor = self.db.execute(sql, [f"%{query}%", f"%{query}%", limit])
            rows = cursor.fetchall()
            
            papers = []
            for row in rows:
                try:
                    # Convert row to dict with table context
                    row_dict = self._row_to_dict(row, 'papers')
                    if row_dict:  # Only proceed if conversion was successful
                        paper = self._safe_create_paper(row_dict)
                        if paper:  # Only add if paper creation was successful
                            papers.append(paper)
                except Exception as e:
                    logger.warning(f"Error processing paper row: {e}")
                    continue
            
            logger.info(f"Found {len(papers)} papers for query: '{query}'")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []
    
    def get_all_papers(self) -> List[Paper]:
        """Get all papers with enhanced error handling"""
        try:
            papers = []
            # Use raw SQL for consistency
            cursor = self.db.execute("SELECT * FROM papers ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            for row in rows:
                try:
                    row_dict = self._row_to_dict(row, 'papers')
                    if row_dict:
                        paper = self._safe_create_paper(row_dict)
                        if paper:
                            papers.append(paper)
                except Exception as e:
                    logger.warning(f"Error processing paper row: {e}")
                    continue
                    
            logger.info(f"Retrieved {len(papers)} papers")
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
            cursor = self.db.execute(
                "SELECT * FROM research_notes WHERE paper_id = ?", 
                [paper_id]
            )
            rows = cursor.fetchall()
            
            notes = []
            for row in rows:
                try:
                    row_dict = self._row_to_dict(row, 'research_notes')
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
            
            cursor = self.db.execute(sql, params)
            rows = cursor.fetchall()
            
            themes = []
            for row in rows:
                try:
                    row_dict = self._row_to_dict(row, 'research_themes')
                    if row_dict:
                        theme = ResearchTheme(**row_dict)
                        themes.append(theme)
                except Exception as e:
                    logger.warning(f"Error creating theme from row: {e}")
                    continue
            
            logger.info(f"Retrieved {len(themes)} themes")
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
            cursor = self.db.execute(
                "SELECT * FROM citations WHERE paper_id = ?", 
                [paper_id]
            )
            row = cursor.fetchone()
            
            if row:
                row_dict = self._row_to_dict(row, 'citations')
                if row_dict:
                    return Citation(**row_dict)
            return None
            
        except Exception as e:
            logger.error(f"Error getting citation for paper {paper_id}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        try:
            stats = {}
            tables = ['papers', 'research_notes', 'research_themes', 'citations']
            
            for table in tables:
                try:
                    cursor = self.db.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[table.replace('research_', '')] = count
                except Exception as e:
                    logger.error(f"Error getting count for {table}: {e}")
                    stats[table.replace('research_', '')] = 0
                    
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def diagnose_data_issues(self):
        """Diagnose and log data issues for debugging"""
        try:
            logger.info("Running database diagnostics...")
            
            # Check papers table
            cursor = self.db.execute("SELECT COUNT(*) FROM papers")
            paper_count = cursor.fetchone()[0]
            logger.info(f"Total papers in database: {paper_count}")
            
            if paper_count > 0:
                # Sample a few papers to check for issues
                cursor = self.db.execute("SELECT * FROM papers LIMIT 5")
                sample_rows = cursor.fetchall()
                
                valid_papers = 0
                for i, row in enumerate(sample_rows):
                    try:
                        row_dict = self._row_to_dict(row, 'papers')
                        paper = self._safe_create_paper(row_dict)
                        if paper:
                            valid_papers += 1
                            logger.info(f"Sample paper {i+1}: {paper.title[:50]}...")
                        else:
                            logger.warning(f"Sample paper {i+1}: Failed to create Paper object")
                    except Exception as e:
                        logger.error(f"Sample paper {i+1}: Error - {e}")
                
                logger.info(f"Valid papers in sample: {valid_papers}/{len(sample_rows)}")
            
            # Check column structure
            cursor = self.db.execute("PRAGMA table_info(papers)")
            columns = cursor.fetchall()
            logger.info(f"Papers table columns: {[col[1] for col in columns]}")
            
        except Exception as e:
            logger.error(f"Error during diagnostics: {e}")
    
    def clear_corrupted_data(self):
        """Clear potentially corrupted data - use with caution"""
        try:
            # Check for and clean up malformed rows
            logger.info("Checking for corrupted data...")
            
            # Test each table for corruption
            tables = ['papers', 'research_notes', 'research_themes', 'citations']
            for table_name in tables:
                try:
                    cursor = self.db.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    clean_rows = []
                    corrupted_count = 0
                    
                    for row in rows:
                        try:
                            # Try to convert each row
                            row_dict = self._row_to_dict(row, table_name)
                            if row_dict:
                                if table_name == 'papers':
                                    paper = self._safe_create_paper(row_dict)
                                    if paper:
                                        clean_rows.append(row_dict)
                                    else:
                                        corrupted_count += 1
                                else:
                                    clean_rows.append(row_dict)
                            else:
                                corrupted_count += 1
                        except Exception:
                            corrupted_count += 1
                    
                    if corrupted_count > 0:
                        logger.warning(f"Found {corrupted_count} corrupted rows in {table_name}")
                    else:
                        logger.info(f"Table {table_name} is clean ({len(clean_rows)} rows)")
                        
                except Exception as e:
                    logger.error(f"Error checking table {table_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error during corruption check: {e}")
    
    def test_data_retrieval(self):
        """Test data retrieval to diagnose issues"""
        logger.info("Testing data retrieval...")
        
        try:
            # Run diagnostics first
            self.diagnose_data_issues()
            
            # Test raw counts
            stats = self.get_stats()
            logger.info(f"Database stats: {stats}")
            
            # Test themes retrieval
            themes = self.get_themes(min_frequency=0)  # Get all themes
            logger.info(f"Retrieved {len(themes)} themes")
            
            if themes:
                logger.info(f"Sample theme: {themes[0].title}")
            
            # Test papers search
            papers = self.search_papers("quantum", limit=5)
            logger.info(f"Found {len(papers)} papers for 'quantum' search")
            
            if papers:
                logger.info(f"Sample paper: {papers[0].title}")
                
        except Exception as e:
            logger.error(f"Error during data retrieval test: {e}")

# Global database instance
db = DatabaseManager()