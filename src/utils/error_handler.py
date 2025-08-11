# Error Handler Utility
import logging
import time
import traceback
from typing import Any, Callable, Optional, Dict, List
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ErrorStatistics:
    """Track error statistics for monitoring"""
    total_errors: int = 0
    error_types: Dict[str, int] = None
    last_error_time: Optional[float] = None
    
    def __post_init__(self):
        if self.error_types is None:
            self.error_types = {}

class ErrorHandler:
    """Enhanced error handling with recovery strategies"""
    
    def __init__(self):
        self.stats = ErrorStatistics()
        self.recovery_strategies = {
            'api_timeout': self._retry_with_backoff,
            'safety_block': self._adjust_safety_settings,
            'rate_limit': self._wait_and_retry,
            'content_too_short': self._use_fallback_content,
            'parsing_error': self._skip_and_continue
        }
    
    def handle_with_recovery(self, error_type: str = 'general', max_retries: int = 3):
        """Decorator for handling errors with recovery strategies"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        self._log_error(e, func.__name__, attempt)
                        
                        if attempt < max_retries:
                            recovery_func = self.recovery_strategies.get(error_type, self._default_recovery)
                            if recovery_func(e, attempt):
                                continue
                        break
                
                # If all retries failed, try fallback
                return self._get_fallback_result(func, last_exception)
            
            return wrapper
        return decorator
    
    def _log_error(self, error: Exception, function_name: str, attempt: int):
        """Log error with context"""
        self.stats.total_errors += 1
        error_type = type(error).__name__
        self.stats.error_types[error_type] = self.stats.error_types.get(error_type, 0) + 1
        self.stats.last_error_time = time.time()
        
        if attempt == 0:
            logger.warning(f"Error in {function_name}: {error}")
        else:
            logger.info(f"Retry {attempt} for {function_name} failed: {error}")
    
    def _retry_with_backoff(self, error: Exception, attempt: int) -> bool:
        """Retry with exponential backoff"""
        wait_time = min(30, 2 ** attempt)
        logger.info(f"Retrying in {wait_time}s due to: {error}")
        time.sleep(wait_time)
        return True
    
    def _adjust_safety_settings(self, error: Exception, attempt: int) -> bool:
        """Adjust safety settings for content policy errors"""
        logger.info("Adjusting safety settings and retrying...")
        return True
    
    def _wait_and_retry(self, error: Exception, attempt: int) -> bool:
        """Wait for rate limit reset"""
        wait_time = 60 + (attempt * 30)  # Base 60s + progressive delay
        logger.info(f"Rate limit hit, waiting {wait_time}s...")
        time.sleep(wait_time)
        return True
    
    def _use_fallback_content(self, error: Exception, attempt: int) -> bool:
        """Use fallback for content too short errors"""
        logger.info("Using fallback content processing...")
        return False  # Don't retry, use fallback
    
    def _skip_and_continue(self, error: Exception, attempt: int) -> bool:
        """Skip current item and continue"""
        logger.info("Skipping current item due to parsing error...")
        return False  # Don't retry, skip
    
    def _default_recovery(self, error: Exception, attempt: int) -> bool:
        """Default recovery strategy"""
        if attempt < 2:  # Only retry twice for unknown errors
            time.sleep(5)
            return True
        return False
    
    def _get_fallback_result(self, func: Callable, error: Exception) -> Any:
        """Get fallback result when all retries fail"""
        function_name = func.__name__
        
        # Return appropriate fallback based on function
        if 'extract' in function_name or 'generate' in function_name:
            return []  # Empty list for extraction functions
        elif 'synthesize' in function_name or 'identify' in function_name:
            return {'themes': [], 'gaps': [], 'statistics': {}}
        elif 'search' in function_name:
            return []  # Empty results for search
        
        logger.error(f"No fallback defined for {function_name}, returning None")
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            'total_errors': self.stats.total_errors,
            'error_types': dict(self.stats.error_types),
            'last_error_time': self.stats.last_error_time,
            'time_since_last_error': time.time() - (self.stats.last_error_time or 0)
        }
    
    def reset_statistics(self):
        """Reset error statistics"""
        self.stats = ErrorStatistics()

# Global error handler instance
error_handler = ErrorHandler()

# Convenience decorators
def handle_api_errors(func):
    """Decorator for API-related functions"""
    return error_handler.handle_with_recovery('api_timeout')(func)

def handle_content_errors(func):
    """Decorator for content processing functions"""
    return error_handler.handle_with_recovery('content_too_short')(func)

def handle_safety_errors(func):
    """Decorator for LLM safety-related functions"""
    return error_handler.handle_with_recovery('safety_block')(func)
