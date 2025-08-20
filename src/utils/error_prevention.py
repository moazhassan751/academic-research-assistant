"""
Comprehensive Error Prevention and Recovery System
Monitors application health and prevents common errors
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import traceback

logger = logging.getLogger(__name__)

@dataclass
class ErrorMetrics:
    """Track error metrics for monitoring"""
    total_errors: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)
    last_error_time: Optional[datetime] = None
    error_rate_1min: float = 0.0
    error_rate_5min: float = 0.0
    recent_errors: List[Dict] = field(default_factory=list)

class ErrorPreventionSystem:
    """System to prevent and recover from common errors"""
    
    def __init__(self):
        self.metrics = ErrorMetrics()
        self.error_handlers = {}
        self.health_checks = {}
        self.recovery_strategies = {}
        self.monitoring_enabled = True
        self.lock = threading.Lock()
        
        # Initialize default handlers
        self._setup_default_handlers()
        
        # Start monitoring thread
        if self.monitoring_enabled:
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def _setup_default_handlers(self):
        """Setup default error handlers"""
        
        # KeyError handlers
        self.register_error_handler(
            KeyError,
            self._handle_key_error,
            "Missing dictionary key - using safe access patterns"
        )
        
        # AttributeError handlers  
        self.register_error_handler(
            AttributeError,
            self._handle_attribute_error,
            "Missing object attribute - using getattr with defaults"
        )
        
        # Network error handlers
        self.register_error_handler(
            ConnectionError,
            self._handle_connection_error,
            "Network connectivity issues - implementing retry logic"
        )
        
        # Import error handlers
        self.register_error_handler(
            ImportError,
            self._handle_import_error,
            "Missing dependencies - providing fallbacks"
        )
    
    def register_error_handler(self, error_type: type, handler: Callable, description: str):
        """Register a custom error handler"""
        self.error_handlers[error_type] = {
            'handler': handler,
            'description': description,
            'count': 0,
            'last_triggered': None
        }
    
    def register_health_check(self, name: str, check_func: Callable, interval: int = 60):
        """Register a health check function"""
        self.health_checks[name] = {
            'function': check_func,
            'interval': interval,
            'last_check': None,
            'status': 'unknown',
            'consecutive_failures': 0
        }
    
    def register_recovery_strategy(self, condition: str, strategy: Callable, description: str):
        """Register an automatic recovery strategy"""
        self.recovery_strategies[condition] = {
            'strategy': strategy,
            'description': description,
            'executions': 0,
            'last_executed': None
        }
    
    def safe_execute(self, func: Callable, *args, fallback=None, **kwargs):
        """Execute function with comprehensive error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self._record_error(e, func.__name__ if hasattr(func, '__name__') else str(func))
            
            # Try registered handler
            error_type = type(e)
            if error_type in self.error_handlers:
                handler_info = self.error_handlers[error_type]
                handler_info['count'] += 1
                handler_info['last_triggered'] = datetime.now()
                
                try:
                    return handler_info['handler'](e, func, *args, **kwargs)
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")
            
            # Use fallback if provided
            if fallback is not None:
                if callable(fallback):
                    try:
                        return fallback(*args, **kwargs)
                    except Exception:
                        return None
                else:
                    return fallback
            
            # Re-raise if no handler or fallback
            raise e
    
    def _record_error(self, error: Exception, context: str = ""):
        """Record error metrics"""
        with self.lock:
            self.metrics.total_errors += 1
            error_type = type(error).__name__
            self.metrics.error_types[error_type] = self.metrics.error_types.get(error_type, 0) + 1
            self.metrics.last_error_time = datetime.now()
            
            # Add to recent errors (keep last 100)
            error_record = {
                'timestamp': datetime.now().isoformat(),
                'type': error_type,
                'message': str(error),
                'context': context,
                'traceback': traceback.format_exc()
            }
            self.metrics.recent_errors.append(error_record)
            if len(self.metrics.recent_errors) > 100:
                self.metrics.recent_errors = self.metrics.recent_errors[-100:]
    
    def _handle_key_error(self, error: KeyError, func: Callable, *args, **kwargs):
        """Handle KeyError with safe dictionary access"""
        logger.warning(f"KeyError in {func.__name__}: {error}")
        # Return empty dict or safe default based on context
        if 'get_stats' in str(func):
            return {'papers': 0, 'notes': 0, 'themes': 0, 'citations': 0}
        return {}
    
    def _handle_attribute_error(self, error: AttributeError, func: Callable, *args, **kwargs):
        """Handle AttributeError with safe attribute access"""
        logger.warning(f"AttributeError in {func.__name__}: {error}")
        # Could try to add missing attributes dynamically
        return None
    
    def _handle_connection_error(self, error: ConnectionError, func: Callable, *args, **kwargs):
        """Handle connection errors with retry logic"""
        logger.warning(f"ConnectionError in {func.__name__}: {error}")
        
        # Implement exponential backoff retry
        for attempt in range(3):
            time.sleep(2 ** attempt)
            try:
                return func(*args, **kwargs)
            except ConnectionError:
                if attempt == 2:  # Last attempt
                    logger.error(f"All retry attempts failed for {func.__name__}")
                    return None
                continue
    
    def _handle_import_error(self, error: ImportError, func: Callable, *args, **kwargs):
        """Handle import errors with fallbacks"""
        logger.warning(f"ImportError in {func.__name__}: {error}")
        # Return a minimal fallback or None
        return None
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_enabled:
            try:
                self._run_health_checks()
                self._calculate_error_rates()
                self._trigger_recovery_strategies()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on monitor errors
    
    def _run_health_checks(self):
        """Run registered health checks"""
        current_time = datetime.now()
        
        for name, check_info in self.health_checks.items():
            # Check if it's time to run this health check
            if (check_info['last_check'] is None or 
                current_time - check_info['last_check'] >= timedelta(seconds=check_info['interval'])):
                
                try:
                    result = check_info['function']()
                    check_info['status'] = 'healthy' if result else 'unhealthy'
                    check_info['consecutive_failures'] = 0 if result else check_info['consecutive_failures'] + 1
                    check_info['last_check'] = current_time
                    
                    if check_info['consecutive_failures'] >= 3:
                        logger.warning(f"Health check '{name}' has failed {check_info['consecutive_failures']} times")
                        
                except Exception as e:
                    logger.error(f"Health check '{name}' failed with error: {e}")
                    check_info['status'] = 'error'
                    check_info['consecutive_failures'] += 1
                    check_info['last_check'] = current_time
    
    def _calculate_error_rates(self):
        """Calculate error rates for monitoring"""
        current_time = datetime.now()
        one_min_ago = current_time - timedelta(minutes=1)
        five_min_ago = current_time - timedelta(minutes=5)
        
        recent_1min = [e for e in self.metrics.recent_errors 
                      if datetime.fromisoformat(e['timestamp']) > one_min_ago]
        recent_5min = [e for e in self.metrics.recent_errors 
                      if datetime.fromisoformat(e['timestamp']) > five_min_ago]
        
        self.metrics.error_rate_1min = len(recent_1min)
        self.metrics.error_rate_5min = len(recent_5min) / 5.0
    
    def _trigger_recovery_strategies(self):
        """Trigger automatic recovery strategies based on conditions"""
        # High error rate recovery
        if self.metrics.error_rate_1min > 10:  # More than 10 errors per minute
            if 'high_error_rate' in self.recovery_strategies:
                strategy = self.recovery_strategies['high_error_rate']
                if (strategy['last_executed'] is None or 
                    datetime.now() - strategy['last_executed'] > timedelta(minutes=5)):
                    
                    logger.warning("High error rate detected, triggering recovery strategy")
                    try:
                        strategy['strategy']()
                        strategy['executions'] += 1
                        strategy['last_executed'] = datetime.now()
                    except Exception as e:
                        logger.error(f"Recovery strategy failed: {e}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        current_time = datetime.now()
        
        return {
            'timestamp': current_time.isoformat(),
            'error_metrics': {
                'total_errors': self.metrics.total_errors,
                'error_rate_1min': self.metrics.error_rate_1min,
                'error_rate_5min': self.metrics.error_rate_5min,
                'error_types': self.metrics.error_types,
                'last_error': self.metrics.last_error_time.isoformat() if self.metrics.last_error_time else None
            },
            'health_checks': {
                name: {
                    'status': info['status'],
                    'consecutive_failures': info['consecutive_failures'],
                    'last_check': info['last_check'].isoformat() if info['last_check'] else None
                }
                for name, info in self.health_checks.items()
            },
            'error_handlers': {
                error_type.__name__: {
                    'description': info['description'],
                    'trigger_count': info['count'],
                    'last_triggered': info['last_triggered'].isoformat() if info['last_triggered'] else None
                }
                for error_type, info in self.error_handlers.items()
            }
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent errors for debugging"""
        return self.metrics.recent_errors[-limit:]
    
    def reset_metrics(self):
        """Reset error metrics"""
        with self.lock:
            self.metrics = ErrorMetrics()

# Global instance
error_prevention = ErrorPreventionSystem()

# Convenience functions
def safe_execute(func: Callable, *args, fallback=None, **kwargs):
    """Global safe execute function"""
    return error_prevention.safe_execute(func, *args, fallback=fallback, **kwargs)

def get_health_report() -> Dict[str, Any]:
    """Get global health report"""
    return error_prevention.get_health_report()

def register_health_check(name: str, check_func: Callable, interval: int = 60):
    """Register a global health check"""
    return error_prevention.register_health_check(name, check_func, interval)
