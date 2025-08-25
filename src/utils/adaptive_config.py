"""
Performance-optimized configuration system that adapts to system resources
and workload patterns for the academic research assistant.
"""

import json
import psutil
import multiprocessing
from pathlib import Path
from typing import Dict, Any, Optional, List
import time
from dataclasses import dataclass, asdict

from ..utils.app_logging import logger

@dataclass
class PerformanceConfig:
    """Performance configuration settings"""
    # Database settings
    db_connection_pool_size: int = 10
    db_cache_size_mb: int = 50
    db_optimize_interval_hours: int = 24
    
    # QA Agent settings
    max_papers_context: int = 12
    max_context_length: int = 8000
    parallel_workers: int = 4
    cache_ttl_hours: int = 24
    min_relevance_score: float = 0.2
    
    # API settings
    api_max_concurrent: int = 8
    api_timeout_seconds: int = 30
    api_retry_attempts: int = 3
    
    # Memory management
    max_cache_size_mb: int = 500
    gc_frequency_minutes: int = 30
    
    # Processing settings
    batch_size: int = 50
    chunk_size: int = 1000
    enable_async_processing: bool = True
    
    # Feature toggles
    enable_semantic_search: bool = True
    enable_bm25_scoring: bool = True
    enable_caching: bool = True
    enable_parallel_processing: bool = True


class AdaptiveConfigManager:
    """Manages performance configuration with system adaptation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/performance.json"
        self.config_dir = Path(self.config_path).parent
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # System information
        self.cpu_count = multiprocessing.cpu_count()
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        self.disk_total_gb = psutil.disk_usage('/').total / (1024**3)
        
        # Load or create configuration
        self.performance_config = self._load_or_create_config()
        
        # Adaptation tracking
        self.last_adaptation = time.time()
        self.adaptation_interval = 3600  # 1 hour
        
        logger.info(f"Adaptive config manager initialized: "
                   f"{self.cpu_count} CPUs, {self.memory_gb:.1f}GB RAM")
    
    def _load_or_create_config(self) -> PerformanceConfig:
        """Load existing config or create optimized default"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Create config from loaded data
                config = PerformanceConfig(**config_data)
                logger.info(f"Loaded performance configuration from {self.config_path}")
                return config
                
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
        
        # Create system-optimized default configuration
        config = self._create_optimized_config()
        self._save_config(config)
        return config
    
    def _create_optimized_config(self) -> PerformanceConfig:
        """Create performance configuration optimized for current system"""
        logger.info("Creating system-optimized performance configuration")
        
        # Base configuration
        config = PerformanceConfig()
        
        # CPU-based optimizations
        if self.cpu_count >= 8:
            # High-end system
            config.parallel_workers = min(12, self.cpu_count)
            config.api_max_concurrent = min(16, self.cpu_count * 2)
            config.batch_size = 100
        elif self.cpu_count >= 4:
            # Mid-range system
            config.parallel_workers = min(8, self.cpu_count)
            config.api_max_concurrent = min(12, self.cpu_count * 2)
            config.batch_size = 75
        else:
            # Low-end system
            config.parallel_workers = max(2, self.cpu_count)
            config.api_max_concurrent = max(4, self.cpu_count)
            config.batch_size = 25
            config.max_papers_context = 8  # Reduce context for performance
        
        # Memory-based optimizations
        if self.memory_gb >= 16:
            # High memory
            config.db_cache_size_mb = 200
            config.max_cache_size_mb = 1000
            config.db_connection_pool_size = 20
            config.max_context_length = 12000
        elif self.memory_gb >= 8:
            # Medium memory
            config.db_cache_size_mb = 100
            config.max_cache_size_mb = 500
            config.db_connection_pool_size = 15
            config.max_context_length = 8000
        else:
            # Low memory
            config.db_cache_size_mb = 50
            config.max_cache_size_mb = 200
            config.db_connection_pool_size = 8
            config.max_context_length = 4000
            config.cache_ttl_hours = 12  # Shorter cache to save memory
            config.gc_frequency_minutes = 15  # More frequent GC
        
        # Feature optimization based on system capabilities
        if self.memory_gb < 4:
            config.enable_semantic_search = False  # Disable heavy features
            config.enable_bm25_scoring = False
        
        # Disk-based optimizations
        if self.disk_total_gb < 50:
            config.db_optimize_interval_hours = 48  # Less frequent optimization
        
        logger.info(f"Optimized config created: {config.parallel_workers} workers, "
                   f"{config.db_cache_size_mb}MB cache, {config.max_papers_context} papers")
        
        return config
    
    def adapt_to_current_load(self) -> bool:
        """Adapt configuration based on current system load"""
        if time.time() - self.last_adaptation < self.adaptation_interval:
            return False  # Too soon to adapt
        
        try:
            # Get current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_io = psutil.disk_io_counters()
            
            adapted = False
            
            # CPU load adaptation
            if cpu_percent > 85:
                # High CPU load - reduce parallelism
                if self.performance_config.parallel_workers > 2:
                    self.performance_config.parallel_workers = max(
                        2, self.performance_config.parallel_workers - 1
                    )
                    adapted = True
                    logger.info(f"Reduced parallel workers to {self.performance_config.parallel_workers}")
            
            elif cpu_percent < 30 and self.performance_config.parallel_workers < self.cpu_count:
                # Low CPU load - increase parallelism
                self.performance_config.parallel_workers = min(
                    self.cpu_count, self.performance_config.parallel_workers + 1
                )
                adapted = True
                logger.info(f"Increased parallel workers to {self.performance_config.parallel_workers}")
            
            # Memory load adaptation
            if memory_percent > 90:
                # High memory pressure - reduce cache sizes
                self.performance_config.max_cache_size_mb = max(
                    100, int(self.performance_config.max_cache_size_mb * 0.8)
                )
                self.performance_config.db_cache_size_mb = max(
                    25, int(self.performance_config.db_cache_size_mb * 0.8)
                )
                adapted = True
                logger.info("Reduced cache sizes due to memory pressure")
            
            elif memory_percent < 50:
                # Low memory usage - can increase cache sizes
                max_cache = int(self.memory_gb * 50)  # 50MB per GB of RAM
                if self.performance_config.max_cache_size_mb < max_cache:
                    self.performance_config.max_cache_size_mb = min(
                        max_cache, int(self.performance_config.max_cache_size_mb * 1.2)
                    )
                    adapted = True
                    logger.info(f"Increased cache size to {self.performance_config.max_cache_size_mb}MB")
            
            if adapted:
                self._save_config(self.performance_config)
                self.last_adaptation = time.time()
            
            return adapted
            
        except Exception as e:
            logger.error(f"Load adaptation error: {e}")
            return False
    
    def optimize_for_workload(self, workload_type: str) -> bool:
        """Optimize configuration for specific workload type"""
        try:
            original_config = PerformanceConfig(**asdict(self.performance_config))
            
            if workload_type == 'research_heavy':
                # Many paper retrievals and searches
                self.performance_config.max_papers_context = min(20, self.cpu_count * 2)
                self.performance_config.db_connection_pool_size = min(25, self.cpu_count * 3)
                self.performance_config.batch_size = min(200, self.cpu_count * 20)
                self.performance_config.cache_ttl_hours = 48  # Longer cache for research
                
            elif workload_type == 'qa_intensive':
                # Many questions, need fast responses
                self.performance_config.max_papers_context = 8  # Smaller context for speed
                self.performance_config.max_context_length = 6000
                self.performance_config.parallel_workers = min(16, self.cpu_count * 2)
                self.performance_config.cache_ttl_hours = 12  # Shorter cache for freshness
                
            elif workload_type == 'batch_processing':
                # Large batch operations
                self.performance_config.batch_size = min(500, self.cpu_count * 50)
                self.performance_config.parallel_workers = self.cpu_count
                self.performance_config.enable_async_processing = True
                self.performance_config.db_connection_pool_size = self.cpu_count * 2
                
            elif workload_type == 'memory_constrained':
                # Low memory system
                self.performance_config.max_papers_context = 5
                self.performance_config.max_context_length = 3000
                self.performance_config.max_cache_size_mb = 100
                self.performance_config.db_cache_size_mb = 25
                self.performance_config.gc_frequency_minutes = 10
                
            elif workload_type == 'balanced':
                # Balanced workload
                self.performance_config = self._create_optimized_config()
            
            else:
                logger.warning(f"Unknown workload type: {workload_type}")
                return False
            
            # Save optimized configuration
            self._save_config(self.performance_config)
            
            logger.info(f"Configuration optimized for {workload_type} workload")
            return True
            
        except Exception as e:
            logger.error(f"Workload optimization error: {e}")
            return False
    
    def _save_config(self, config: PerformanceConfig):
        """Save configuration to file"""
        try:
            config_data = asdict(config)
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.debug(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get_config(self) -> PerformanceConfig:
        """Get current performance configuration"""
        return self.performance_config
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        return {
            'cpu_count': self.cpu_count,
            'memory_gb': self.memory_gb,
            'disk_total_gb': self.disk_total_gb,
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    
    def get_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        
        # Check system resources
        if self.memory_gb < 4:
            recommendations.append("Consider upgrading RAM to at least 8GB for better performance")
        
        if self.cpu_count < 4:
            recommendations.append("System may benefit from more CPU cores for parallel processing")
        
        # Check current load
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 80:
                recommendations.append("High CPU usage detected - consider reducing parallel workers")
            
            if memory_percent > 85:
                recommendations.append("High memory usage - consider reducing cache sizes")
            
            if cpu_percent < 20 and memory_percent < 50:
                recommendations.append("System has spare capacity - consider increasing worker counts")
                
        except Exception as e:
            logger.warning(f"Could not get load recommendations: {e}")
        
        return recommendations
    
    def reset_to_default(self):
        """Reset configuration to optimized defaults"""
        self.performance_config = self._create_optimized_config()
        self._save_config(self.performance_config)
        logger.info("Configuration reset to system-optimized defaults")


# Global adaptive config manager
_config_manager = None

def get_adaptive_config() -> AdaptiveConfigManager:
    """Get or create adaptive configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = AdaptiveConfigManager()
    return _config_manager

def get_performance_config() -> PerformanceConfig:
    """Get current performance configuration"""
    return get_adaptive_config().get_config()
