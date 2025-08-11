import sqlite3
import sqlite_utils
import aiosqlite
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
import threading
from contextlib import contextmanager, asynccontextmanager
from .models import Paper, ResearchNote, ResearchTheme, Citation
from ..utils.config import config
from ..utils.logging import logger
from ..utils.database_optimizer import DatabaseOptimizer

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.get('storage.database_path', 'data/research.db')
        
        # Create data directory if it doesn't exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Thread-local storage for database connections
        self._local = threading.local()
        
        # Keep track of column names for each table - initialize BEFORE _initialize_tables()
        self._column_cache = {}
        
        # Initialize database optimizer
        self.optimizer = DatabaseOptimizer(self.db_path)
        
        # Initialize tables using the main thread connection
        self._initialize_tables()
        
        # Run initial optimization
        try:
            self.optimizer.create_indexes()
            logger.info("Database indexes initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize database indexes: {e}")
    
    def _get_db(self) -> sqlite_utils.Database:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'db') or self._local.db is None:
            # Create thread-local connection - removed connect_kwargs for compatibility
            self._local.db = sqlite_utils.Database(self.db_path, recreate=False)
            logger.debug(f"Created thread-local database connection for thread {threading.get_ident()}")
        return self._local.db
    
    def _get_raw_connection(self) -> sqlite3.Connection:
        """Get raw SQLite connection for thread-local use"""
        if not hasattr(self._local, 'raw_conn') or self._local.raw_conn is None:
            self._local.raw_conn = sqlite3.Connection(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            # Enable row factory for named access
            self._local.raw_conn.row_factory = sqlite3.Row
            logger.debug(f"Created thread-local raw connection for thread {threading.get_ident()}")
        return self._local.raw_conn
    
    @contextmanager
    def _transaction(self):
        """Context manager for database transactions with thread safety"""
        conn = self._get_raw_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
    
    def _initialize_tables(self):
        """Initialize database tables with thread safety"""
        try:
            # Use a simple connection for initialization - removed connect_kwargs
            init_db = sqlite_utils.Database(self.db_path)
            
            init_db.executescript("""
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
            self._cache_column_names(init_db)
            
            # Close the initialization connection
            init_db.close()
            
            logger.info(f"Database initialized at: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _cache_column_names(self, db_conn=None):
        """Cache column names for each table to handle raw tuple/list rows"""
        db = db_conn or self._get_db()
        tables = ['papers', 'research_notes', 'research_themes', 'citations']
        
        for table_name in tables:
            try:
                # Get column information
                cursor = db.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]  # Column names are in index 1
                self._column_cache[table_name] = columns
                logger.debug(f"Cached columns for {table_name}: {columns}")
            except Exception as e:
                logger.error(f"Error caching columns for {table_name}: {e}")
                self._column_cache[table_name] = []
    
    def _row_to_dict(self, row, table_name: str = None) -> Dict[str, Any]:
        """Safely convert a database row to dictionary with enhanced thread safety"""
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
                'created_at': row_dict.get('created_at')
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
    
    # Paper operations with thread safety
    def save_paper(self, paper: Paper) -> bool:
        """Save a paper to the database with thread safety"""
        try:
            with self._transaction():
                db = self._get_db()
                db['papers'].insert(paper.to_dict(), replace=True)
                logger.debug(f"Saved paper: {paper.title[:50]}...")
                return True
        except Exception as e:
            logger.error(f"Error saving paper {paper.id}: {e}")
            return False
    
    def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by ID with thread safety"""
        try:
            db = self._get_db()
            try:
                row = db['papers'].get(paper_id)
                if row:
                    row_dict = self._row_to_dict(row, 'papers')
                    return self._safe_create_paper(row_dict)
            except sqlite_utils.db.NotFoundError:
                return None
                
        except Exception as e:
            logger.error(f"Error getting paper {paper_id}: {e}")
            return None
    
    def search_papers(self, query: str, limit: int = 50, sort_by: str = 'relevance') -> List[Paper]:
        """Search papers by title or abstract with sorting and thread safety"""
        try:
            # Build ORDER BY clause based on sort_by parameter
            if sort_by == 'date':
                order_clause = "ORDER BY published_date DESC"
            elif sort_by == 'citations':
                order_clause = "ORDER BY citations DESC"
            else:  # relevance (default)
                order_clause = "ORDER BY citations DESC"
            
            sql = f"""
                SELECT * FROM papers 
                WHERE title LIKE ? OR abstract LIKE ?
                {order_clause}
                LIMIT ?
            """
            
            conn = self._get_raw_connection()
            cursor = conn.execute(sql, [f"%{query}%", f"%{query}%", limit])
            rows = cursor.fetchall()
            
            papers = []
            for row in rows:
                try:
                    # Convert row to dict with table context
                    row_dict = self._row_to_dict(row, 'papers')
                    if row_dict:
                        paper = self._safe_create_paper(row_dict)
                        if paper:
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
        """Get all papers with thread safety"""
        try:
            papers = []
            conn = self._get_raw_connection()
            cursor = conn.execute("SELECT * FROM papers ORDER BY created_at DESC")
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
    
    def get_papers(self) -> List[Paper]:
        """Alias for get_all_papers() for compatibility"""
        return self.get_all_papers()
    
    # Note operations with thread safety
    def save_note(self, note: ResearchNote) -> bool:
        """Save a research note with thread safety"""
        try:
            with self._transaction():
                db = self._get_db()
                db['research_notes'].insert(note.to_dict(), replace=True)
                logger.debug(f"Saved note: {note.id}")
                return True
        except Exception as e:
            logger.error(f"Error saving note {note.id}: {e}")
            return False
    
    def get_notes_for_paper(self, paper_id: str) -> List[ResearchNote]:
        """Get all notes for a specific paper with thread safety"""
        try:
            conn = self._get_raw_connection()
            cursor = conn.execute(
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
    
    def get_all_notes(self) -> List[ResearchNote]:
        """Get all research notes with thread safety"""
        try:
            notes = []
            conn = self._get_raw_connection()
            cursor = conn.execute("SELECT * FROM research_notes ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            for row in rows:
                try:
                    row_dict = self._row_to_dict(row, 'research_notes')
                    if row_dict:
                        note = ResearchNote(**row_dict)
                        notes.append(note)
                except Exception as e:
                    logger.warning(f"Error converting note row: {e}")
                    continue
                    
            logger.info(f"Retrieved {len(notes)} notes")
            return notes
        except Exception as e:
            logger.error(f"Error getting all notes: {e}")
            return []
    
    # Theme operations with thread safety
    def save_theme(self, theme: ResearchTheme) -> bool:
        """Save a research theme with thread safety"""
        try:
            with self._transaction():
                db = self._get_db()
                db['research_themes'].insert(theme.to_dict(), replace=True)
                logger.debug(f"Saved theme: {theme.title}")
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
            
            conn = self._get_raw_connection()
            cursor = conn.execute(sql, params)
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
    
    # Citation operations with thread safety
    def save_citation(self, citation: Citation) -> bool:
        """Save a citation with thread safety"""
        try:
            with self._transaction():
                db = self._get_db()
                db['citations'].insert(citation.to_dict(), replace=True)
                logger.debug(f"Saved citation: {citation.citation_key}")
                return True
        except Exception as e:
            logger.error(f"Error saving citation {citation.id}: {e}")
            return False
    
    def get_citation(self, paper_id: str) -> Optional[Citation]:
        """Get citation for a paper with thread safety"""
        try:
            conn = self._get_raw_connection()
            cursor = conn.execute(
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
        """Get database statistics with thread safety"""
        try:
            stats = {}
            tables = ['papers', 'research_notes', 'research_themes', 'citations']
            
            conn = self._get_raw_connection()
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[table.replace('research_', '')] = count
                except Exception as e:
                    logger.error(f"Error getting count for {table}: {e}")
                    stats[table.replace('research_', '')] = 0
                    
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def close_connections(self):
        """Close thread-local connections"""
        try:
            if hasattr(self._local, 'db') and self._local.db is not None:
                self._local.db.close()
                self._local.db = None
                
            if hasattr(self._local, 'raw_conn') and self._local.raw_conn is not None:
                self._local.raw_conn.close()
                self._local.raw_conn = None
                
            logger.debug(f"Closed database connections for thread {threading.get_ident()}")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
    
    def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization and return statistics"""
        try:
            return self.optimizer.maintenance_routine()
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            return self.optimizer.get_database_statistics()
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {'error': str(e)}
    
    def analyze_query_performance(self, query: str) -> List[Dict[str, Any]]:
        """Analyze query performance and get optimization recommendations"""
        try:
            return self.optimizer.get_query_plan(query)
        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            return []
    
    def run_maintenance(self) -> Dict[str, Any]:
        """Run routine database maintenance"""
        logger.info("Starting database maintenance routine...")
        result = self.optimize_database()
        
        if result.get('success', False):
            logger.info("Database maintenance completed successfully")
            
            # Log key statistics
            stats = result.get('statistics', {})
            logger.info(f"Database size: {stats.get('file_size', 0):,} bytes")
            logger.info(f"Total papers: {stats.get('table_counts', {}).get('papers', 0)}")
            logger.info(f"Total notes: {stats.get('table_counts', {}).get('research_notes', 0)}")
            logger.info(f"Active indexes: {stats.get('index_count', 0)}")
        else:
            logger.error(f"Database maintenance failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.close_connections()
        except:
            pass


class AsyncDatabaseManager:
    """Async database manager for improved performance"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.get('storage.database_path', 'data/research.db')
        
        # Create data directory if it doesn't exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize optimizer
        self.optimizer = DatabaseOptimizer(self.db_path)
        
        # Connection pool (simple implementation)
        self._connection_pool = []
        self._pool_size = 5
        self._pool_lock = asyncio.Lock()
        
        # Initialize database schema synchronously first
        self._initialize_tables_sync()
    
    def _initialize_tables_sync(self):
        """Initialize database tables synchronously"""
        # Use the existing DatabaseManager to initialize schema
        sync_db = DatabaseManager(self.db_path)
        # Schema is already initialized by DatabaseManager
        del sync_db
    
    @asynccontextmanager
    async def _get_connection(self):
        """Get connection from pool or create new one"""
        async with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
            else:
                conn = await aiosqlite.connect(
                    self.db_path,
                    timeout=30.0
                )
                conn.row_factory = aiosqlite.Row
        
        try:
            yield conn
        finally:
            async with self._pool_lock:
                if len(self._connection_pool) < self._pool_size:
                    self._connection_pool.append(conn)
                else:
                    await conn.close()
    
    async def save_papers_async(self, papers: List[Paper]) -> List[str]:
        """Save multiple papers asynchronously"""
        saved_ids = []
        
        async with self._get_connection() as conn:
            # Begin transaction
            await conn.execute("BEGIN")
            
            try:
                for paper in papers:
                    # Check if paper exists
                    async with conn.execute(
                        "SELECT id FROM papers WHERE id = ?", (paper.id,)
                    ) as cursor:
                        exists = await cursor.fetchone()
                    
                    if not exists:
                        await conn.execute("""
                            INSERT INTO papers (
                                id, title, authors, abstract, url, published_date,
                                venue, citations, pdf_path, full_text, keywords,
                                doi, arxiv_id, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            paper.id, paper.title, paper.authors, paper.abstract,
                            paper.url, paper.published_date, paper.venue, paper.citations,
                            paper.pdf_path, paper.full_text, paper.keywords,
                            paper.doi, paper.arxiv_id, paper.created_at
                        ))
                        saved_ids.append(paper.id)
                        logger.debug(f"Saved paper: {paper.title}")
                
                await conn.commit()
                
            except Exception as e:
                await conn.rollback()
                logger.error(f"Failed to save papers: {e}")
                raise
        
        logger.info(f"Saved {len(saved_ids)} papers asynchronously")
        return saved_ids
    
    async def save_notes_async(self, notes: List[ResearchNote]) -> List[str]:
        """Save multiple research notes asynchronously"""
        saved_ids = []
        
        async with self._get_connection() as conn:
            await conn.execute("BEGIN")
            
            try:
                for note in notes:
                    async with conn.execute(
                        "SELECT id FROM research_notes WHERE id = ?", (note.id,)
                    ) as cursor:
                        exists = await cursor.fetchone()
                    
                    if not exists:
                        await conn.execute("""
                            INSERT INTO research_notes (
                                id, paper_id, content, note_type, confidence,
                                page_number, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            note.id, note.paper_id, note.content, note.note_type,
                            note.confidence, note.page_number, note.created_at
                        ))
                        saved_ids.append(note.id)
                
                await conn.commit()
                
            except Exception as e:
                await conn.rollback()
                logger.error(f"Failed to save notes: {e}")
                raise
        
        logger.info(f"Saved {len(saved_ids)} notes asynchronously")
        return saved_ids
    
    async def get_papers_async(
        self, 
        limit: Optional[int] = None,
        search_query: Optional[str] = None
    ) -> List[Paper]:
        """Get papers asynchronously with optional search"""
        papers = []
        
        async with self._get_connection() as conn:
            if search_query:
                query = """
                    SELECT * FROM papers 
                    WHERE title LIKE ? OR abstract LIKE ? OR authors LIKE ?
                    ORDER BY citations DESC, published_date DESC
                """
                params = [f"%{search_query}%"] * 3
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                async with conn.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
            else:
                query = "SELECT * FROM papers ORDER BY citations DESC, published_date DESC"
                params = []
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                async with conn.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
            
            for row in rows:
                papers.append(Paper(
                    id=row['id'],
                    title=row['title'],
                    authors=row['authors'],
                    abstract=row['abstract'],
                    url=row['url'],
                    published_date=row['published_date'],
                    venue=row['venue'],
                    citations=row['citations'] or 0,
                    pdf_path=row['pdf_path'],
                    full_text=row['full_text'],
                    keywords=row['keywords'],
                    doi=row['doi'],
                    arxiv_id=row['arxiv_id'],
                    created_at=row['created_at']
                ))
        
        return papers
    
    async def get_notes_by_paper_async(self, paper_id: str) -> List[ResearchNote]:
        """Get notes for a specific paper asynchronously"""
        notes = []
        
        async with self._get_connection() as conn:
            async with conn.execute(
                "SELECT * FROM research_notes WHERE paper_id = ? ORDER BY created_at",
                (paper_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                
                for row in rows:
                    notes.append(ResearchNote(
                        id=row['id'],
                        paper_id=row['paper_id'],
                        content=row['content'],
                        note_type=row['note_type'],
                        confidence=row['confidence'] or 0.0,
                        page_number=row['page_number'],
                        created_at=row['created_at']
                    ))
        
        return notes
    
    async def get_database_stats_async(self) -> Dict[str, Any]:
        """Get database statistics asynchronously"""
        stats = {}
        
        async with self._get_connection() as conn:
            # Get table counts
            for table in ['papers', 'research_notes', 'research_themes', 'citations']:
                async with conn.execute(f"SELECT COUNT(*) FROM {table}") as cursor:
                    result = await cursor.fetchone()
                    stats[f'{table}_count'] = result[0] if result else 0
            
            # Get recent activity
            async with conn.execute(
                "SELECT COUNT(*) FROM papers WHERE created_at > datetime('now', '-7 days')"
            ) as cursor:
                result = await cursor.fetchone()
                stats['papers_last_week'] = result[0] if result else 0
            
            # Get top venues
            async with conn.execute("""
                SELECT venue, COUNT(*) as count 
                FROM papers 
                WHERE venue IS NOT NULL 
                GROUP BY venue 
                ORDER BY count DESC 
                LIMIT 5
            """) as cursor:
                venues = await cursor.fetchall()
                stats['top_venues'] = [{'venue': row[0], 'count': row[1]} for row in venues]
        
        return stats
    
    async def search_papers_fulltext_async(
        self, 
        query: str, 
        limit: int = 50
    ) -> List[Paper]:
        """Full-text search across papers asynchronously"""
        papers = []
        
        # Use MATCH for FTS if available, otherwise LIKE
        search_query = """
            SELECT *, 
                   (CASE 
                    WHEN title LIKE ? THEN 10
                    WHEN abstract LIKE ? THEN 5
                    WHEN authors LIKE ? THEN 3
                    ELSE 1 END) as relevance_score
            FROM papers 
            WHERE title LIKE ? OR abstract LIKE ? OR authors LIKE ? OR full_text LIKE ?
            ORDER BY relevance_score DESC, citations DESC
            LIMIT ?
        """
        
        search_term = f"%{query}%"
        params = [search_term] * 7 + [limit]
        
        async with self._get_connection() as conn:
            async with conn.execute(search_query, params) as cursor:
                rows = await cursor.fetchall()
                
                for row in rows:
                    papers.append(Paper(
                        id=row['id'],
                        title=row['title'],
                        authors=row['authors'],
                        abstract=row['abstract'],
                        url=row['url'],
                        published_date=row['published_date'],
                        venue=row['venue'],
                        citations=row['citations'] or 0,
                        pdf_path=row['pdf_path'],
                        full_text=row['full_text'],
                        keywords=row['keywords'],
                        doi=row['doi'],
                        arxiv_id=row['arxiv_id'],
                        created_at=row['created_at']
                    ))
        
        return papers
    
    async def optimize_database_async(self) -> Dict[str, Any]:
        """Run database optimization asynchronously"""
        # Run optimization in background to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Run optimizer in thread pool to avoid blocking
        result = await loop.run_in_executor(
            None, 
            self.optimizer.maintenance_routine
        )
        
        return result
    
    async def close_connections(self):
        """Close all connections in pool"""
        async with self._pool_lock:
            for conn in self._connection_pool:
                await conn.close()
            self._connection_pool.clear()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_connections()


# Create singleton instances
db_manager = DatabaseManager()
async_db_manager = AsyncDatabaseManager()

# Global database instance
db = DatabaseManager()