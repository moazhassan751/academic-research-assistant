"""
Enhanced error handling system for Academic Research Assistant
"""

import logging
import traceback
import sys
import time
import functools
import asyncio
from typing import Any, Callable, Dict, List, Optional, Type, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
import json

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur"""
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    FILE_ERROR = "file_error"
    PARSING_ERROR = "parsing_error"
    CONFIGURATION_ERROR = "configuration_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for errors"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    function_name: Optional[str] = None
    module_name: Optional[str] = None
    traceback_str: Optional[str] = None
    user_message: Optional[str] = None
    recovery_suggestions: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary"""
        return {
            'error_type': self.error_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'function_name': self.function_name,
            'module_name': self.module_name,
            'traceback': self.traceback_str,
            'user_message': self.user_message,
            'recovery_suggestions': self.recovery_suggestions
        }
    
    def to_json(self) -> str:
        """Convert error context to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class ResearchAssistantError(Exception):
    """Base exception for research assistant errors"""
    
    def __init__(
        self, 
        message: str, 
        error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.error_context = ErrorContext(
            error_type=error_type,
            severity=severity,
            message=message,
            details=details or {},
            user_message=user_message,
            recovery_suggestions=recovery_suggestions or [],
            traceback_str=traceback.format_exc()
        )


class APIError(ResearchAssistantError):
    """API-related errors"""
    
    def __init__(
        self, 
        message: str, 
        api_name: str = None,
        status_code: int = None,
        response_data: Any = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        details.update({
            'api_name': api_name,
            'status_code': status_code,
            'response_data': response_data
        })
        
        super().__init__(
            message,
            error_type=ErrorType.API_ERROR,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message=f"API request failed: {message}",
            recovery_suggestions=[
                "Check your internet connection",
                "Verify API credentials and rate limits",
                "Try again in a few minutes"
            ],
            **kwargs
        )
        # Add message attribute for compatibility
        self.message = message


class DatabaseError(ResearchAssistantError):
    """Database-related errors"""
    
    def __init__(self, message: str, operation: str = None, table: str = None, **kwargs):
        details = kwargs.get('details', {})
        details.update({
            'operation': operation,
            'table': table
        })
        
        super().__init__(
            message,
            error_type=ErrorType.DATABASE_ERROR,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message="Database operation failed",
            recovery_suggestions=[
                "Check database file permissions",
                "Verify database integrity",
                "Try restarting the application"
            ],
            **kwargs
        )
        # Add message attribute for compatibility
        self.message = message


class ValidationError(ResearchAssistantError):
    """Validation-related errors"""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        details = kwargs.get('details', {})
        details.update({
            'field': field,
            'value': str(value) if value is not None else None
        })
        
        super().__init__(
            message,
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=f"Invalid input: {message}",
            recovery_suggestions=[
                "Check your input format",
                "Refer to the documentation for valid values",
                "Try with a simpler query"
            ],
            **kwargs
        )
        # Add message attribute for compatibility
        self.message = message


class ConfigurationError(ResearchAssistantError):
    """Configuration-related errors"""
    
    def __init__(self, message: str, config_key: str = None, config_file: str = None, **kwargs):
        details = kwargs.get('details', {})
        details.update({
            'config_key': config_key,
            'config_file': config_file
        })
        
        super().__init__(
            message,
            error_type=ErrorType.CONFIGURATION_ERROR,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message=f"Configuration error: {message}",
            recovery_suggestions=[
                "Check your configuration file",
                "Verify environment variables",
                "Reset to default configuration"
            ],
            **kwargs
        )
        # Add message attribute for compatibility
        self.message = message


class NetworkError(ResearchAssistantError):
    """Network-related errors"""
    
    def __init__(self, message: str, url: str = None, **kwargs):
        details = kwargs.get('details', {})
        details.update({'url': url})
        
        super().__init__(
            message,
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message="Network connection failed",
            recovery_suggestions=[
                "Check your internet connection",
                "Try again in a few minutes",
                "Check if the service is currently available"
            ],
            **kwargs
        )
        # Add message attribute for compatibility
        self.message = message


class ErrorHandler:
    """Central error handling system"""
    
    def __init__(self, log_to_file: bool = True, log_file: str = None):
        self.log_to_file = log_to_file
        self.log_file = log_file or "logs/errors.log"
        self.error_counts = {}
        self.recent_errors = []
        self.max_recent_errors = 100
        
        # Set up error logging
        self._setup_error_logging()
    
    def _setup_error_logging(self):
        """Set up error-specific logging"""
        error_logger = logging.getLogger('error_handler')
        
        if self.log_to_file:
            # Create error log handler
            from pathlib import Path
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
            
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            error_logger.addHandler(handler)
            error_logger.setLevel(logging.ERROR)
    
    def handle_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """Handle an error and return error context"""
        
        # Create error context based on error type
        if isinstance(error, ResearchAssistantError):
            error_context = error.error_context
        else:
            # Convert generic exception to error context
            error_context = self._create_error_context(error, context)
        
        # Add function and module information
        frame = sys._getframe(1)
        error_context.function_name = frame.f_code.co_name
        error_context.module_name = frame.f_globals.get('__name__', 'unknown')
        
        # Log the error
        self._log_error(error_context)
        
        # Track error statistics
        self._track_error(error_context)
        
        # Add to recent errors
        self._add_to_recent_errors(error_context)
        
        return error_context
    
    def _create_error_context(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """Create error context from generic exception"""
        
        # Determine error type based on exception type
        error_type = self._classify_error(error)
        
        # Determine severity
        severity = self._determine_severity(error, error_type)
        
        # Create user-friendly message
        user_message = self._create_user_message(error, error_type)
        
        # Generate recovery suggestions
        recovery_suggestions = self._generate_recovery_suggestions(error_type)
        
        return ErrorContext(
            error_type=error_type,
            severity=severity,
            message=str(error),
            details=context or {},
            user_message=user_message,
            recovery_suggestions=recovery_suggestions,
            traceback_str=traceback.format_exc()
        )
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception"""
        error_name = error.__class__.__name__.lower()
        error_message = str(error).lower()
        
        # Classification based on exception type
        if 'connection' in error_name or 'network' in error_name:
            return ErrorType.NETWORK_ERROR
        elif 'timeout' in error_name or 'timeout' in error_message:
            return ErrorType.TIMEOUT_ERROR
        elif 'database' in error_name or 'sql' in error_name:
            return ErrorType.DATABASE_ERROR
        elif 'validation' in error_name or 'invalid' in error_message:
            return ErrorType.VALIDATION_ERROR
        elif 'file' in error_name or 'permission' in error_message:
            return ErrorType.FILE_ERROR
        elif 'parse' in error_name or 'json' in error_name or 'xml' in error_name:
            return ErrorType.PARSING_ERROR
        elif 'auth' in error_name or 'credential' in error_message:
            return ErrorType.AUTHENTICATION_ERROR
        elif 'rate' in error_message and 'limit' in error_message:
            return ErrorType.RATE_LIMIT_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _determine_severity(self, error: Exception, error_type: ErrorType) -> ErrorSeverity:
        """Determine error severity"""
        critical_types = {ErrorType.DATABASE_ERROR, ErrorType.CONFIGURATION_ERROR}
        high_types = {ErrorType.API_ERROR, ErrorType.NETWORK_ERROR, ErrorType.AUTHENTICATION_ERROR}
        
        if error_type in critical_types:
            return ErrorSeverity.CRITICAL
        elif error_type in high_types:
            return ErrorSeverity.HIGH
        elif error_type in {ErrorType.VALIDATION_ERROR, ErrorType.PARSING_ERROR}:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _create_user_message(self, error: Exception, error_type: ErrorType) -> str:
        """Create user-friendly error message"""
        messages = {
            ErrorType.API_ERROR: "Unable to fetch data from external service",
            ErrorType.DATABASE_ERROR: "Database operation failed",
            ErrorType.NETWORK_ERROR: "Network connection problem",
            ErrorType.VALIDATION_ERROR: "Invalid input provided",
            ErrorType.FILE_ERROR: "File operation failed",
            ErrorType.PARSING_ERROR: "Data parsing error",
            ErrorType.TIMEOUT_ERROR: "Operation timed out",
            ErrorType.RATE_LIMIT_ERROR: "Too many requests, please wait",
            ErrorType.AUTHENTICATION_ERROR: "Authentication failed",
        }
        
        return messages.get(error_type, "An unexpected error occurred")
    
    def _generate_recovery_suggestions(self, error_type: ErrorType) -> List[str]:
        """Generate recovery suggestions based on error type"""
        suggestions = {
            ErrorType.API_ERROR: [
                "Check your internet connection",
                "Verify API credentials",
                "Try again in a few minutes"
            ],
            ErrorType.DATABASE_ERROR: [
                "Check database file permissions",
                "Restart the application",
                "Contact support if problem persists"
            ],
            ErrorType.NETWORK_ERROR: [
                "Check your internet connection",
                "Try again later",
                "Check firewall settings"
            ],
            ErrorType.VALIDATION_ERROR: [
                "Check your input format",
                "Refer to documentation",
                "Use simpler search terms"
            ],
            ErrorType.RATE_LIMIT_ERROR: [
                "Wait a few minutes before trying again",
                "Reduce the frequency of requests",
                "Consider upgrading your API plan"
            ],
            ErrorType.TIMEOUT_ERROR: [
                "Try again with a smaller query",
                "Check your internet connection",
                "Wait a moment and retry"
            ]
        }
        
        return suggestions.get(error_type, ["Try again later", "Contact support if problem persists"])
    
    def _log_error(self, error_context: ErrorContext):
        """Log error with appropriate level"""
        error_logger = logging.getLogger('error_handler')
        
        log_message = (
            f"[{error_context.error_type.value.upper()}] "
            f"{error_context.message}"
        )
        
        extra_info = {
            'error_type': error_context.error_type.value,
            'severity': error_context.severity.value,
            'function': error_context.function_name,
            'module': error_context.module_name,
            'details': error_context.details
        }
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            error_logger.critical(log_message, extra=extra_info)
        elif error_context.severity == ErrorSeverity.HIGH:
            error_logger.error(log_message, extra=extra_info)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            error_logger.warning(log_message, extra=extra_info)
        else:
            error_logger.info(log_message, extra=extra_info)
    
    def _track_error(self, error_context: ErrorContext):
        """Track error statistics"""
        error_key = f"{error_context.error_type.value}:{error_context.severity.value}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def _add_to_recent_errors(self, error_context: ErrorContext):
        """Add error to recent errors list"""
        self.recent_errors.append(error_context)
        
        # Keep only recent errors
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors = self.recent_errors[-self.max_recent_errors:]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts.copy(),
            'recent_error_count': len(self.recent_errors),
            'error_types': list(set(
                error.error_type.value for error in self.recent_errors
            )),
            'most_common_error': max(
                self.error_counts.items(), 
                key=lambda x: x[1], 
                default=('none', 0)
            )[0] if self.error_counts else 'none'
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorContext]:
        """Get recent errors"""
        return self.recent_errors[-limit:]
    
    def clear_error_history(self):
        """Clear error history and statistics"""
        self.error_counts.clear()
        self.recent_errors.clear()


# Global error handler instance
error_handler = ErrorHandler()


def handle_errors(
    error_type: Optional[ErrorType] = None,
    severity: Optional[ErrorSeverity] = None,
    reraise: bool = True,
    default_return: Any = None
):
    """Decorator for automatic error handling"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function_args': str(args)[:500],  # Limit length
                    'function_kwargs': str(kwargs)[:500]
                }
                
                # Handle the error
                error_context = error_handler.handle_error(e, context)
                
                # Override error type/severity if specified
                if error_type:
                    error_context.error_type = error_type
                if severity:
                    error_context.severity = severity
                
                if reraise:
                    if isinstance(e, ResearchAssistantError):
                        raise e
                    else:
                        # Convert to ResearchAssistantError
                        raise ResearchAssistantError(
                            str(e),
                            error_type=error_context.error_type,
                            severity=error_context.severity,
                            details=error_context.details
                        )
                else:
                    logger.error(f"Error handled and suppressed: {e}")
                    return default_return
        
        return wrapper
    
    return decorator


def handle_async_errors(
    error_type: Optional[ErrorType] = None,
    severity: Optional[ErrorSeverity] = None,
    reraise: bool = True,
    default_return: Any = None
):
    """Decorator for automatic async error handling"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function_args': str(args)[:500],
                    'function_kwargs': str(kwargs)[:500]
                }
                
                error_context = error_handler.handle_error(e, context)
                
                if error_type:
                    error_context.error_type = error_type
                if severity:
                    error_context.severity = severity
                
                if reraise:
                    if isinstance(e, ResearchAssistantError):
                        raise e
                    else:
                        raise ResearchAssistantError(
                            str(e),
                            error_type=error_context.error_type,
                            severity=error_context.severity,
                            details=error_context.details
                        )
                else:
                    logger.error(f"Async error handled and suppressed: {e}")
                    return default_return
        
        return wrapper
    
    return decorator


def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any, Optional[ErrorContext]]:
    """Safely execute a function and return (success, result, error_context)"""
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        context = {
            'function_name': func.__name__ if hasattr(func, '__name__') else str(func),
            'args': str(args)[:200],
            'kwargs': str(kwargs)[:200]
        }
        error_context = error_handler.handle_error(e, context)
        return False, None, error_context


async def safe_execute_async(func: Callable, *args, **kwargs) -> tuple[bool, Any, Optional[ErrorContext]]:
    """Safely execute an async function and return (success, result, error_context)"""
    try:
        result = await func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        context = {
            'function_name': func.__name__ if hasattr(func, '__name__') else str(func),
            'args': str(args)[:200],
            'kwargs': str(kwargs)[:200]
        }
        error_context = error_handler.handle_error(e, context)
        return False, None, error_context


class ErrorRecoveryManager:
    """Manages error recovery strategies"""
    
    def __init__(self):
        self.recovery_strategies = {
            ErrorType.API_ERROR: self._recover_api_error,
            ErrorType.NETWORK_ERROR: self._recover_network_error,
            ErrorType.DATABASE_ERROR: self._recover_database_error,
            ErrorType.RATE_LIMIT_ERROR: self._recover_rate_limit_error,
        }
    
    async def attempt_recovery(
        self, 
        error_context: ErrorContext, 
        original_func: Callable, 
        *args, 
        **kwargs
    ) -> tuple[bool, Any]:
        """Attempt to recover from error and retry operation"""
        
        recovery_func = self.recovery_strategies.get(error_context.error_type)
        
        if recovery_func:
            logger.info(f"Attempting recovery for {error_context.error_type.value}")
            
            recovery_success = await recovery_func(error_context)
            
            if recovery_success:
                logger.info("Recovery successful, retrying operation")
                try:
                    if asyncio.iscoroutinefunction(original_func):
                        result = await original_func(*args, **kwargs)
                    else:
                        result = original_func(*args, **kwargs)
                    return True, result
                except Exception as e:
                    logger.error(f"Retry failed after recovery: {e}")
                    return False, None
        
        logger.warning(f"No recovery strategy for {error_context.error_type.value}")
        return False, None
    
    async def _recover_api_error(self, error_context: ErrorContext) -> bool:
        """Attempt to recover from API error"""
        # Wait before retrying
        await asyncio.sleep(2)
        return True
    
    async def _recover_network_error(self, error_context: ErrorContext) -> bool:
        """Attempt to recover from network error"""
        # Wait longer for network issues
        await asyncio.sleep(5)
        return True
    
    async def _recover_database_error(self, error_context: ErrorContext) -> bool:
        """Attempt to recover from database error"""
        # For database errors, we might need to recreate connections
        logger.info("Attempting database connection recovery")
        # This would be implemented based on specific database setup
        return False
    
    async def _recover_rate_limit_error(self, error_context: ErrorContext) -> bool:
        """Attempt to recover from rate limit error"""
        # Wait longer for rate limit recovery
        await asyncio.sleep(60)
        return True


# Global error recovery manager
recovery_manager = ErrorRecoveryManager()


# Legacy support for existing error handling
@dataclass
class ErrorStatistics:
    """Track error statistics for monitoring (legacy compatibility)"""
    total_errors: int = 0
    error_types: Dict[str, int] = None
    last_error_time: Optional[float] = None
    
    def __post_init__(self):
        if self.error_types is None:
            self.error_types = {}


def with_error_handling(
    operation_name: str = "Unknown",
    error_types: tuple = (Exception,),
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """Legacy error handling decorator (now enhanced)"""
    def decorator(func: Callable) -> Callable:
        return handle_errors(reraise=True)(func)
    return decorator


async def handle_with_retry(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    error_types: tuple = (Exception,),
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """Legacy retry function (now enhanced with new error handling)"""
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except error_types as e:
            last_error = e
            
            if attempt < max_retries:
                wait_time = delay * (backoff_factor ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            else:
                # Final attempt failed, handle with new error system
                error_context = error_handler.handle_error(e, context)
                raise ResearchAssistantError(
                    f"Max retries exceeded: {str(e)}",
                    error_type=error_context.error_type,
                    severity=error_context.severity,
                    details=error_context.details
                )
    
    return None

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
