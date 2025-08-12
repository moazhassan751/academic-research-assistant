"""
Enhanced database optimization utilities for Academic Research Assistant
"""

import sqlite3
import aiosqlite
import asyncio
import logging
import time
import threading
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager, asynccontextmanager
from collections import defaultdict
import json

from .performance_optimizer import optimizer

logger = logging.getLogger(__name__)


class EnhancedDatabaseOptimizer:
    """Advanced database optimization with performance monitoring and adaptive tuning"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.stats_cache = {}
        self._optimization_lock = threading.Lock()
        
        # Performance tracking
        self.query_stats = defaultdict(list)
        self.index_usage = defaultdict(int)
        self.optimization_history = []
        
    def create_advanced_indexes(self) -> Dict[str, Any]:
        """Create comprehensive indexes with performance monitoring"""
        results = {'created': [], 'failed': [], 'skipped': []}
        
        # Enhanced index definitions with performance hints
        advanced_indexes = [
            # Core performance indexes
            ("idx_papers_title_hash", "CREATE INDEX IF NOT EXISTS idx_papers_title_hash ON papers(title COLLATE NOCASE)", "High"),
            ("idx_papers_authors_normalized", "CREATE INDEX IF NOT EXISTS idx_papers_authors_normalized ON papers(LOWER(authors))", "High"),
            ("idx_papers_published_date_desc", "CREATE INDEX IF NOT EXISTS idx_papers_published_date_desc ON papers(published_date DESC)", "High"),
            ("idx_papers_venue_normalized", "CREATE INDEX IF NOT EXISTS idx_papers_venue_normalized ON papers(LOWER(venue))", "Medium"),
            ("idx_papers_citations_desc", "CREATE INDEX IF NOT EXISTS idx_papers_citations_desc ON papers(citations DESC)", "High"),
            ("idx_papers_doi_unique", "CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_doi_unique ON papers(doi) WHERE doi IS NOT NULL", "High"),
            ("idx_papers_arxiv_unique", "CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_arxiv_unique ON papers(arxiv_id) WHERE arxiv_id IS NOT NULL", "High"),
            
            # Time-based indexes for performance
            ("idx_papers_created_at_desc", "CREATE INDEX IF NOT EXISTS idx_papers_created_at_desc ON papers(created_at DESC)", "Medium"),
            ("idx_papers_recent", "CREATE INDEX IF NOT EXISTS idx_papers_recent ON papers(published_date) WHERE published_date >= '2020-01-01'", "High"),
            
            # Research notes optimized indexes
            ("idx_notes_paper_id_type", "CREATE INDEX IF NOT EXISTS idx_notes_paper_id_type ON research_notes(paper_id, note_type)", "High"),
            ("idx_notes_confidence_desc", "CREATE INDEX IF NOT EXISTS idx_notes_confidence_desc ON research_notes(confidence DESC)", "Medium"),
            ("idx_notes_content_length", "CREATE INDEX IF NOT EXISTS idx_notes_content_length ON research_notes(LENGTH(content) DESC)", "Low"),
            
            # Research themes advanced indexes
            ("idx_themes_frequency_confidence", "CREATE INDEX IF NOT EXISTS idx_themes_frequency_confidence ON research_themes(frequency DESC, confidence DESC)", "High"),
            ("idx_themes_title_unique", "CREATE UNIQUE INDEX IF NOT EXISTS idx_themes_title_unique ON research_themes(title COLLATE NOCASE)", "Medium"),
            
            # Citations performance indexes
            ("idx_citations_paper_format", "CREATE INDEX IF NOT EXISTS idx_citations_paper_format ON citations(paper_id, citation_key)", "High"),
            
            # Full-text search optimizations
            ("idx_papers_abstract_words", "CREATE INDEX IF NOT EXISTS idx_papers_abstract_words ON papers(abstract) WHERE LENGTH(abstract) > 100", "Medium"),
            ("idx_notes_content_words", "CREATE INDEX IF NOT EXISTS idx_notes_content_words ON research_notes(content) WHERE LENGTH(content) > 50", "Medium"),
            
            # Composite performance indexes for common query patterns
            ("idx_papers_search_rank", "CREATE INDEX IF NOT EXISTS idx_papers_search_rank ON papers(published_date DESC, citations DESC, venue)", "High"),
            ("idx_papers_quality_score", "CREATE INDEX IF NOT EXISTS idx_papers_quality_score ON papers(citations DESC, LENGTH(abstract) DESC)", "Medium"),
            ("idx_notes_paper_confidence", "CREATE INDEX IF NOT EXISTS idx_notes_paper_confidence ON research_notes(paper_id, confidence DESC, note_type)", "High"),
            
            # Partial indexes for better performance
            ("idx_papers_high_citations", "CREATE INDEX IF NOT EXISTS idx_papers_high_citations ON papers(title, authors) WHERE citations >= 10", "Medium"),
            ("idx_papers_with_doi", "CREATE INDEX IF NOT EXISTS idx_papers_with_doi ON papers(doi, published_date) WHERE doi IS NOT NULL", "High"),
            ("idx_papers_with_abstract", "CREATE INDEX IF NOT EXISTS idx_papers_with_abstract ON papers(title, authors) WHERE abstract IS NOT NULL AND LENGTH(abstract) > 100", "Medium"),
        ]
        
        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            cursor = conn.cursor()
            
            for index_name, index_sql, priority in advanced_indexes:
                try:
                    start_time = time.time()
                    cursor.execute(index_sql)
                    creation_time = time.time() - start_time
                    
                    results['created'].append({
                        'name': index_name,
                        'sql': index_sql,
                        'priority': priority,
                        'creation_time': creation_time
                    })
                    
                    logger.debug(f"Created {priority} priority index {index_name} in {creation_time:.3f}s")
                    
                except sqlite3.Error as e:
                    error_msg = f"Failed to create index {index_name}: {e}"
                    results['failed'].append({'name': index_name, 'error': str(e)})
                    logger.warning(error_msg)
            
            conn.commit()
            
        logger.info(f"Advanced indexes: {len(results['created'])} created, {len(results['failed'])} failed")
        return results

    @contextmanager 
    def measure_query_performance(self, operation_name: str):
        """Measure and log query performance"""
        start_time = time.perf_counter()
        start_memory = optimizer.get_performance_summary()['system_info']['current_memory_percent']
        
        try:
            yield
        finally:
            execution_time = time.perf_counter() - start_time
            end_memory = optimizer.get_performance_summary()['system_info']['current_memory_percent']
            
            self.query_stats[operation_name].append({
                'execution_time': execution_time,
                'memory_delta': end_memory - start_memory,
                'timestamp': time.time()
            })
            
            # Log slow queries
            if execution_time > 1.0:
                logger.warning(f"Slow query {operation_name}: {execution_time:.3f}s")

    def optimize_database_comprehensive(self) -> Dict[str, Any]:
        """Run comprehensive database optimization with performance monitoring"""
        with self._optimization_lock:
            optimization_start = time.time()
            results = {
                'started_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'operations': [],
                'performance_gains': {},
                'warnings': []
            }
            
            with sqlite3.connect(self.db_path, timeout=60.0) as conn:
                cursor = conn.cursor()
                
                # Get baseline metrics
                baseline_stats = self._get_database_stats(cursor)
                results['baseline'] = baseline_stats
                
                # 1. Analyze database for query optimization
                try:
                    with self.measure_query_performance('analyze'):
                        cursor.execute("ANALYZE")
                    results['operations'].append({'analyze': 'completed'})
                except Exception as e:
                    results['warnings'].append(f"ANALYZE failed: {e}")
                
                # 2. Update statistics for query planner
                try:
                    cursor.execute("PRAGMA optimize")
                    results['operations'].append({'optimize': 'completed'})
                except Exception as e:
                    results['warnings'].append(f"PRAGMA optimize failed: {e}")
                
                # 3. Apply advanced performance pragmas
                performance_pragmas = [
                    ("journal_mode", "WAL"),           # Write-Ahead Logging
                    ("synchronous", "NORMAL"),         # Balanced safety/speed  
                    ("cache_size", "20000"),           # 20MB cache
                    ("temp_store", "MEMORY"),          # Temp tables in memory
                    ("mmap_size", "268435456"),        # 256MB memory map
                    ("page_size", "4096"),             # Optimal page size
                    ("auto_vacuum", "INCREMENTAL"),    # Incremental vacuuming
                    ("secure_delete", "OFF"),          # Faster deletes
                    ("count_changes", "OFF"),          # Disable change counting
                    ("query_only", "OFF"),             # Allow writes
                    ("threads", str(min(4, optimizer.cpu_count))),  # Multi-threading
                ]
                
                applied_pragmas = []
                for pragma_name, pragma_value in performance_pragmas:
                    try:
                        cursor.execute(f"PRAGMA {pragma_name}={pragma_value}")
                        applied_pragmas.append(f"{pragma_name}={pragma_value}")
                    except Exception as e:
                        results['warnings'].append(f"PRAGMA {pragma_name} failed: {e}")
                
                results['operations'].append({'pragmas_applied': applied_pragmas})
                
                # 4. Vacuum if needed (only if database is fragmented)
                try:
                    cursor.execute("PRAGMA freelist_count")
                    freelist_count = cursor.fetchone()[0]
                    
                    if freelist_count > 1000:  # Significant fragmentation
                        logger.info("Database fragmentation detected, running VACUUM...")
                        with self.measure_query_performance('vacuum'):
                            cursor.execute("VACUUM")
                        results['operations'].append({'vacuum': f'completed (freed {freelist_count} pages)'})
                    else:
                        results['operations'].append({'vacuum': 'skipped (minimal fragmentation)'})
                        
                except Exception as e:
                    results['warnings'].append(f"VACUUM operation failed: {e}")
                
                # 5. Create/update advanced indexes
                index_results = self.create_advanced_indexes()
                results['operations'].append({'indexes': index_results})
                
                # Get post-optimization metrics
                final_stats = self._get_database_stats(cursor)
                results['final'] = final_stats
                
                # Calculate performance improvements
                if baseline_stats and final_stats:
                    results['performance_gains'] = {
                        'page_count_change': final_stats.get('page_count', 0) - baseline_stats.get('page_count', 0),
                        'freelist_reduction': baseline_stats.get('freelist_count', 0) - final_stats.get('freelist_count', 0),
                        'cache_efficiency': final_stats.get('cache_size', 0) / max(baseline_stats.get('cache_size', 1), 1)
                    }
            
            optimization_time = time.time() - optimization_start
            results['total_time'] = optimization_time
            results['completed_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Store optimization history
            self.optimization_history.append(results)
            
            logger.info(f"Database optimization completed in {optimization_time:.2f}s")
            return results

    def _get_database_stats(self, cursor) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = {}
        
        try:
            # Basic database info
            pragmas_to_check = ['page_count', 'freelist_count', 'cache_size', 'journal_mode', 'synchronous']
            for pragma in pragmas_to_check:
                try:
                    cursor.execute(f"PRAGMA {pragma}")
                    result = cursor.fetchone()
                    stats[pragma] = result[0] if result else None
                except:
                    pass
            
            # Table statistics
            cursor.execute("""
                SELECT name, COUNT(*) as count 
                FROM sqlite_master 
                WHERE type='table' 
                GROUP BY name
            """)
            stats['table_count'] = len(cursor.fetchall())
            
            # Index statistics
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='index'
            """)
            stats['index_count'] = cursor.fetchone()[0]
            
            # Database size
            stats['file_size'] = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            
        except Exception as e:
            logger.debug(f"Error getting database stats: {e}")
            
        return stats

    async def optimize_async_connections(self, connection_pool_size: int = 10) -> Dict[str, Any]:
        """Optimize async database connections for better performance"""
        results = {
            'pool_size': connection_pool_size,
            'optimizations_applied': [],
            'performance_settings': {}
        }
        
        # Optimal connection settings for async operations
        async_optimizations = [
            ("journal_mode", "WAL"),
            ("synchronous", "NORMAL"),
            ("cache_size", "15000"),  # 15MB for async operations
            ("temp_store", "MEMORY"),
            ("mmap_size", "536870912"),  # 512MB for large datasets
            ("threadsafe", "1"),
            ("read_uncommitted", "1"),  # For read-heavy workloads
        ]
        
        try:
            async with aiosqlite.connect(self.db_path, timeout=30.0) as conn:
                for setting_name, setting_value in async_optimizations:
                    try:
                        await conn.execute(f"PRAGMA {setting_name}={setting_value}")
                        results['optimizations_applied'].append(f"{setting_name}={setting_value}")
                    except Exception as e:
                        logger.debug(f"Async optimization {setting_name} failed: {e}")
                
                await conn.commit()
                
                # Test connection performance
                start_time = time.time()
                await conn.execute("SELECT 1")
                response_time = time.time() - start_time
                
                results['performance_settings'] = {
                    'connection_test_time': response_time,
                    'optimizations_count': len(results['optimizations_applied'])
                }
                
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Async database optimization failed: {e}")
        
        return results

    def get_query_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive query performance report"""
        report = {
            'total_queries': sum(len(queries) for queries in self.query_stats.values()),
            'operations': {},
            'slow_queries': [],
            'recommendations': []
        }
        
        for operation, queries in self.query_stats.items():
            if not queries:
                continue
                
            times = [q['execution_time'] for q in queries]
            memory_deltas = [q['memory_delta'] for q in queries]
            
            operation_stats = {
                'count': len(queries),
                'avg_time': sum(times) / len(times),
                'max_time': max(times),
                'min_time': min(times),
                'avg_memory_delta': sum(memory_deltas) / len(memory_deltas),
                'total_time': sum(times)
            }
            
            report['operations'][operation] = operation_stats
            
            # Identify slow queries
            for query in queries:
                if query['execution_time'] > 2.0:  # Slower than 2 seconds
                    report['slow_queries'].append({
                        'operation': operation,
                        'time': query['execution_time'],
                        'memory_delta': query['memory_delta']
                    })
        
        # Generate recommendations
        if report['slow_queries']:
            report['recommendations'].append("Consider adding indexes for slow queries")
        
        avg_times = [op['avg_time'] for op in report['operations'].values()]
        if avg_times and max(avg_times) > 1.0:
            report['recommendations'].append("Database optimization recommended")
        
        return report

    def maintenance_routine(self) -> Dict[str, Any]:
        """Comprehensive maintenance routine for optimal performance"""
        with optimizer.measure_performance('database_maintenance'):
            maintenance_results = {}
            
            # Step 1: Performance analysis
            maintenance_results['performance_report'] = self.get_query_performance_report()
            
            # Step 2: Database optimization
            maintenance_results['optimization'] = self.optimize_database_comprehensive()
            
            # Step 3: Clear old statistics (keep last 1000 entries per operation)
            cleaned_stats = 0
            for operation in self.query_stats:
                if len(self.query_stats[operation]) > 1000:
                    # Keep newest 1000 entries
                    self.query_stats[operation] = sorted(
                        self.query_stats[operation], 
                        key=lambda x: x['timestamp']
                    )[-1000:]
                    cleaned_stats += 1
            
            maintenance_results['stats_cleanup'] = {'operations_cleaned': cleaned_stats}
            
            # Step 4: Memory cleanup
            collected = optimizer.optimize_gc(aggressive=True)
            maintenance_results['memory_cleanup'] = {'objects_collected': collected}
            
            logger.info("Database maintenance routine completed")
            return maintenance_results

    def create_indexes(self) -> None:
        """Legacy method - redirects to enhanced version"""
        results = self.create_advanced_indexes()
        logger.info(f"Indexes created: {len(results['created'])}")


# Backward compatibility alias
class DatabaseOptimizer(EnhancedDatabaseOptimizer):
    """Legacy alias for backward compatibility"""
    
    def create_indexes(self) -> None:
        """Legacy method - redirects to enhanced version"""
        results = self.create_advanced_indexes()
        logger.info(f"Indexes created: {len(results['created'])}")
    
    def optimize_database(self) -> Dict[str, Any]:
        """Legacy method - redirects to enhanced version"""
        results = self.optimize_database_comprehensive()
        return {
            'analyze_completed': 'analyze' in str(results.get('operations', [])),
            'vacuum_completed': 'vacuum' in str(results.get('operations', [])),
            'optimize_completed': 'optimize' in str(results.get('operations', [])),
            'pragma_optimizations': len(results.get('operations', [])),
            'total_time': results.get('total_time', 0)
        }
