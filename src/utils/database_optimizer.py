"""
Database optimization utilities for Academic Research Assistant
"""

import sqlite3
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization and indexing utilities"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def create_indexes(self) -> None:
        """Create indexes to improve query performance"""
        indexes = [
            # Papers table indexes
            "CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title)",
            "CREATE INDEX IF NOT EXISTS idx_papers_authors ON papers(authors)",
            "CREATE INDEX IF NOT EXISTS idx_papers_published_date ON papers(published_date)",
            "CREATE INDEX IF NOT EXISTS idx_papers_venue ON papers(venue)",
            "CREATE INDEX IF NOT EXISTS idx_papers_citations ON papers(citations DESC)",
            "CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi)",
            "CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id)",
            "CREATE INDEX IF NOT EXISTS idx_papers_created_at ON papers(created_at)",
            
            # Research notes indexes
            "CREATE INDEX IF NOT EXISTS idx_notes_paper_id ON research_notes(paper_id)",
            "CREATE INDEX IF NOT EXISTS idx_notes_note_type ON research_notes(note_type)",
            "CREATE INDEX IF NOT EXISTS idx_notes_confidence ON research_notes(confidence DESC)",
            "CREATE INDEX IF NOT EXISTS idx_notes_created_at ON research_notes(created_at)",
            
            # Research themes indexes
            "CREATE INDEX IF NOT EXISTS idx_themes_frequency ON research_themes(frequency DESC)",
            "CREATE INDEX IF NOT EXISTS idx_themes_confidence ON research_themes(confidence DESC)",
            "CREATE INDEX IF NOT EXISTS idx_themes_created_at ON research_themes(created_at)",
            
            # Citations indexes
            "CREATE INDEX IF NOT EXISTS idx_citations_paper_id ON citations(paper_id)",
            "CREATE INDEX IF NOT EXISTS idx_citations_key ON citations(citation_key)",
            
            # Full-text search indexes
            "CREATE INDEX IF NOT EXISTS idx_papers_title_fts ON papers(title COLLATE NOCASE)",
            "CREATE INDEX IF NOT EXISTS idx_papers_abstract_fts ON papers(abstract COLLATE NOCASE)",
            "CREATE INDEX IF NOT EXISTS idx_notes_content_fts ON research_notes(content COLLATE NOCASE)",
            
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_papers_date_citations ON papers(published_date, citations DESC)",
            "CREATE INDEX IF NOT EXISTS idx_notes_paper_type ON research_notes(paper_id, note_type)",
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    logger.debug(f"Created index: {index_sql}")
                except sqlite3.Error as e:
                    logger.warning(f"Failed to create index: {e}")
            
            conn.commit()
            logger.info(f"Database indexes created/updated for {self.db_path}")
    
    def optimize_database(self) -> Dict[str, Any]:
        """Run comprehensive database optimization"""
        stats = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get initial stats
            stats['initial_size'] = Path(self.db_path).stat().st_size
            
            try:
                # Analyze database for query optimization
                cursor.execute("ANALYZE")
                stats['analyze_completed'] = True
                
                # Vacuum database to reclaim space and defragment
                cursor.execute("VACUUM")
                stats['vacuum_completed'] = True
                
                # Update table statistics
                cursor.execute("PRAGMA optimize")
                stats['optimize_completed'] = True
                
                # Set optimal pragmas
                optimizations = [
                    "PRAGMA journal_mode=WAL",  # Write-Ahead Logging for better concurrency
                    "PRAGMA synchronous=NORMAL",  # Balance between speed and safety
                    "PRAGMA cache_size=10000",  # 10MB cache (default is 2MB)
                    "PRAGMA temp_store=MEMORY",  # Store temp tables in memory
                    "PRAGMA mmap_size=268435456",  # 256MB memory map
                ]
                
                for pragma in optimizations:
                    cursor.execute(pragma)
                
                stats['pragma_optimizations'] = len(optimizations)
                
            except sqlite3.Error as e:
                logger.error(f"Database optimization error: {e}")
                stats['error'] = str(e)
            
            # Get final stats
            stats['final_size'] = Path(self.db_path).stat().st_size
            stats['size_reduction'] = stats['initial_size'] - stats['final_size']
            
            # Get database statistics
            cursor.execute("PRAGMA page_count")
            stats['page_count'] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size")
            stats['page_size'] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA freelist_count")
            stats['free_pages'] = cursor.fetchone()[0]
        
        logger.info(f"Database optimization completed: {stats}")
        return stats
    
    def get_query_plan(self, query: str) -> List[Dict[str, Any]]:
        """Get query execution plan for optimization analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get query plan
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()
            
            # Convert to structured format
            structured_plan = []
            for row in plan:
                structured_plan.append({
                    'id': row[0],
                    'parent': row[1],
                    'notused': row[2],
                    'detail': row[3]
                })
            
            return structured_plan
    
    def analyze_slow_queries(self) -> Dict[str, Any]:
        """Analyze potentially slow queries and suggest optimizations"""
        slow_query_patterns = [
            # Queries without indexes
            "SELECT * FROM papers WHERE title LIKE '%search%'",
            "SELECT * FROM research_notes WHERE content LIKE '%keyword%'",
            "SELECT * FROM papers WHERE published_date > '2020-01-01' ORDER BY citations DESC",
            "SELECT * FROM research_notes WHERE paper_id IN (SELECT id FROM papers WHERE venue = 'Nature')",
            
            # Aggregation queries
            "SELECT COUNT(*) FROM papers WHERE published_date > '2020-01-01'",
            "SELECT venue, COUNT(*) FROM papers GROUP BY venue ORDER BY COUNT(*) DESC",
            "SELECT note_type, AVG(confidence) FROM research_notes GROUP BY note_type",
        ]
        
        analysis = {'queries': []}
        
        for query in slow_query_patterns:
            try:
                plan = self.get_query_plan(query)
                
                # Analyze plan for potential issues
                uses_index = any('USING INDEX' in step['detail'] for step in plan)
                has_scan = any('SCAN TABLE' in step['detail'] for step in plan)
                
                analysis['queries'].append({
                    'query': query,
                    'uses_index': uses_index,
                    'has_table_scan': has_scan,
                    'plan': plan,
                    'recommendation': self._get_optimization_recommendation(plan)
                })
                
            except sqlite3.Error as e:
                logger.warning(f"Could not analyze query {query}: {e}")
        
        return analysis
    
    def _get_optimization_recommendation(self, plan: List[Dict[str, Any]]) -> str:
        """Get optimization recommendation based on query plan"""
        recommendations = []
        
        for step in plan:
            detail = step['detail']
            
            if 'SCAN TABLE' in detail:
                recommendations.append("Consider adding an index to avoid full table scan")
            
            if 'TEMP B-TREE' in detail:
                recommendations.append("Consider adding an index to avoid temporary sorting")
            
            if 'USING INDEX' not in detail and ('WHERE' in detail or 'ORDER BY' in detail):
                recommendations.append("Query might benefit from a composite index")
        
        return "; ".join(recommendations) if recommendations else "Query appears optimized"
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table row counts
            tables = ['papers', 'research_notes', 'research_themes', 'citations']
            stats['table_counts'] = {}
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats['table_counts'][table] = count
                except sqlite3.Error:
                    stats['table_counts'][table] = 0
            
            # Database size info
            stats['file_size'] = Path(self.db_path).stat().st_size
            
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            stats['total_pages'] = page_count
            stats['page_size'] = page_size
            stats['database_size'] = page_count * page_size
            
            cursor.execute("PRAGMA freelist_count")
            stats['free_pages'] = cursor.fetchone()[0]
            stats['free_space'] = stats['free_pages'] * page_size
            
            # Index information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
            stats['indexes'] = [row[0] for row in cursor.fetchall()]
            stats['index_count'] = len(stats['indexes'])
            
            # Journal mode and other settings
            cursor.execute("PRAGMA journal_mode")
            stats['journal_mode'] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA synchronous")
            stats['synchronous'] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA cache_size")
            stats['cache_size'] = cursor.fetchone()[0]
        
        return stats
    
    def maintenance_routine(self) -> Dict[str, Any]:
        """Run routine database maintenance"""
        results = {}
        
        try:
            # Create/update indexes
            self.create_indexes()
            results['indexes_updated'] = True
            
            # Optimize database
            optimization_stats = self.optimize_database()
            results['optimization'] = optimization_stats
            
            # Get final statistics
            results['statistics'] = self.get_database_statistics()
            
            results['success'] = True
            results['message'] = "Database maintenance completed successfully"
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            logger.error(f"Database maintenance failed: {e}")
        
        return results
