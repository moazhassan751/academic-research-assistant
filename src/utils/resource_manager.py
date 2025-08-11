# Smart Resource Manager
import gc
import psutil
import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ResourceManager:
    """Smart resource management for research operations"""
    
    def __init__(self):
        self.memory_threshold = 85.0  # Warning at 85% memory usage
        self.cpu_threshold = 80.0     # Warning at 80% CPU usage
        self.cleanup_threshold = 90.0  # Force cleanup at 90% memory
        self.monitoring_enabled = True
        
    def get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0
    
    def should_cleanup(self) -> bool:
        """Check if cleanup is needed"""
        memory_usage = self.get_memory_usage()
        return memory_usage > self.cleanup_threshold
    
    def force_cleanup(self):
        """Force garbage collection and memory cleanup"""
        try:
            # Clear Python garbage collection
            collected = gc.collect()
            
            # Force memory release
            gc.set_threshold(700, 10, 10)  # More aggressive GC
            
            logger.info(f"Memory cleanup: collected {collected} objects")
            
            # Reset GC thresholds to default after cleanup
            time.sleep(0.1)
            gc.set_threshold(700, 10, 10)
            
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
    
    def smart_batch_size(self, default_size: int = 20, max_papers: int = 50) -> int:
        """Determine optimal batch size based on system resources"""
        memory_usage = self.get_memory_usage()
        
        if memory_usage > 90:
            return min(5, default_size)
        elif memory_usage > 80:
            return min(10, default_size)
        elif memory_usage > 70:
            return min(15, default_size)
        else:
            return default_size
    
    def adaptive_delay(self, base_delay: float = 1.0) -> float:
        """Calculate adaptive delay based on system load"""
        memory_usage = self.get_memory_usage()
        cpu_usage = self.get_cpu_usage()
        
        # Increase delay if system is under stress
        multiplier = 1.0
        
        if memory_usage > 85:
            multiplier += 0.5
        if cpu_usage > 75:
            multiplier += 0.3
        
        return base_delay * multiplier
    
    def monitor_resources(self, operation_name: str = "operation"):
        """Decorator to monitor resource usage during operations"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.monitoring_enabled:
                    return func(*args, **kwargs)
                
                # Pre-operation check
                start_memory = self.get_memory_usage()
                start_time = time.time()
                
                if start_memory > self.memory_threshold:
                    logger.warning(f"High memory usage before {operation_name}: {start_memory:.1f}%")
                
                # Force cleanup if needed
                if self.should_cleanup():
                    logger.info(f"Forcing cleanup before {operation_name}")
                    self.force_cleanup()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Post-operation check
                    end_memory = self.get_memory_usage()
                    duration = time.time() - start_time
                    
                    memory_delta = end_memory - start_memory
                    
                    if memory_delta > 10:
                        logger.warning(f"{operation_name} increased memory by {memory_delta:.1f}% (now {end_memory:.1f}%)")
                    
                    if duration > 60:  # Long operations
                        logger.info(f"{operation_name} completed in {duration:.1f}s (memory: {end_memory:.1f}%)")
                    
                    return result
                    
                except Exception as e:
                    # Cleanup on error
                    self.force_cleanup()
                    raise e
            
            return wrapper
        return decorator
    
    @contextmanager
    def resource_context(self, operation_name: str = "operation"):
        """Context manager for resource monitoring"""
        start_memory = self.get_memory_usage()
        start_time = time.time()
        
        if start_memory > self.memory_threshold:
            logger.warning(f"High memory usage starting {operation_name}: {start_memory:.1f}%")
        
        if self.should_cleanup():
            self.force_cleanup()
        
        try:
            yield
        finally:
            end_memory = self.get_memory_usage()
            duration = time.time() - start_time
            memory_delta = end_memory - start_memory
            
            if memory_delta > 10:
                logger.warning(f"{operation_name} memory impact: +{memory_delta:.1f}% (now {end_memory:.1f}%)")
            
            if end_memory > self.cleanup_threshold:
                logger.info(f"Forcing cleanup after {operation_name}")
                self.force_cleanup()
    
    def get_system_recommendations(self) -> Dict[str, Any]:
        """Get system-specific recommendations"""
        memory_usage = self.get_memory_usage()
        cpu_usage = self.get_cpu_usage()
        
        recommendations = {
            'memory_usage': memory_usage,
            'cpu_usage': cpu_usage,
            'status': 'optimal',
            'suggestions': []
        }
        
        if memory_usage > 95:
            recommendations['status'] = 'critical'
            recommendations['suggestions'].extend([
                'Close unnecessary applications immediately',
                'Restart the research assistant',
                'Use --max-papers 10 or lower',
                'Process research in smaller batches'
            ])
        elif memory_usage > 85:
            recommendations['status'] = 'warning'
            recommendations['suggestions'].extend([
                'Close browser tabs and other applications',
                'Use --max-papers 20 or lower',
                'Consider restarting after large research tasks'
            ])
        elif memory_usage > 70:
            recommendations['status'] = 'caution'
            recommendations['suggestions'].extend([
                'Monitor memory during large research tasks',
                'Consider using --max-papers 30-40 for large topics'
            ])
        
        if cpu_usage > 80:
            recommendations['suggestions'].extend([
                'Wait for current processes to complete',
                'Avoid running multiple research tasks simultaneously',
                'Increase delays between API calls'
            ])
        
        return recommendations
    
    def optimize_for_large_research(self, max_papers: int) -> Dict[str, Any]:
        """Get optimization settings for large research tasks"""
        memory_usage = self.get_memory_usage()
        
        settings = {
            'batch_size': self.smart_batch_size(max_papers=max_papers),
            'delay_multiplier': 1.0,
            'enable_aggressive_cleanup': False,
            'recommended_max_papers': max_papers
        }
        
        if memory_usage > 85:
            settings.update({
                'batch_size': min(5, settings['batch_size']),
                'delay_multiplier': 2.0,
                'enable_aggressive_cleanup': True,
                'recommended_max_papers': min(20, max_papers)
            })
        elif memory_usage > 70:
            settings.update({
                'batch_size': min(10, settings['batch_size']),
                'delay_multiplier': 1.5,
                'recommended_max_papers': min(40, max_papers)
            })
        
        return settings

# Global resource manager instance
resource_manager = ResourceManager()

# Convenience decorators
def monitor_memory(operation_name: str = "operation"):
    """Decorator for memory-intensive operations"""
    return resource_manager.monitor_resources(operation_name)

def with_resource_management(operation_name: str = "operation"):
    """Context manager decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with resource_manager.resource_context(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
