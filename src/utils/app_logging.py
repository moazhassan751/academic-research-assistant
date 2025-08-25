import logging
import logging.handlers
import os
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from rich.logging import RichHandler
from rich.console import Console

# Fix Windows encoding issues
if sys.platform.startswith('win'):
    import codecs
    # Ensure proper UTF-8 encoding for Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'extra_data'):
            log_entry['context'] = record.extra_data
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add process and thread info for debugging
        log_entry['process_id'] = record.process
        log_entry['thread_id'] = record.thread
        
        return json.dumps(log_entry)


class ContextFilter(logging.Filter):
    """Filter to add context information to log records"""
    
    def __init__(self):
        super().__init__()
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set context information for logging"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear context information"""
        self.context.clear()
    
    def filter(self, record):
        """Add context information to the log record"""
        if self.context:
            record.extra_data = self.context.copy()
        return True


class ResearchAssistantLogger:
    """Enhanced logger for Academic Research Assistant"""
    
    def __init__(self, name: str = "research_assistant"):
        self.logger = logging.getLogger(name)
        self.context_filter = ContextFilter()
        self._setup_done = False
    
    def setup_logging(self, log_level: str = None, structured: bool = True):
        """Setup logging with Rich formatting and structured output"""
        if self._setup_done:
            return self.logger
        
        if log_level is None:
            log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Create logs directory
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set logging level
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Add context filter
        self.logger.addFilter(self.context_filter)
        
        # Console handler with Rich formatting
        console_handler = RichHandler(
            rich_tracebacks=True, 
            console=Console(stderr=True),
            show_path=True,
            show_time=True
        )
        console_handler.setLevel(logging.INFO)
        
        # File handler for all logs
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / 'research_assistant.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        if structured:
            # Structured JSON handler for analysis
            json_handler = logging.handlers.RotatingFileHandler(
                logs_dir / 'research_assistant.json',
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=3,
                encoding='utf-8'
            )
            json_handler.setFormatter(StructuredFormatter())
            json_handler.setLevel(logging.INFO)
            self.logger.addHandler(json_handler)
        
        # Regular format for file logs
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # Error handler for critical errors
        error_handler = logging.handlers.RotatingFileHandler(
            logs_dir / 'errors.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
        
        self._setup_done = True
        return self.logger
    
    def set_context(self, **kwargs):
        """Set context for all subsequent log messages"""
        self.context_filter.set_context(**kwargs)
    
    def clear_context(self):
        """Clear logging context"""
        self.context_filter.clear_context()
    
    def log_operation(self, operation: str, **context):
        """Log the start of an operation with context"""
        self.set_context(operation=operation, **context)
        self.logger.info(f"Starting operation: {operation}", extra={'operation_start': True})
    
    def log_operation_complete(self, operation: str, duration: float = None, **results):
        """Log the completion of an operation"""
        log_data = {'operation_complete': True}
        if duration:
            log_data['duration_seconds'] = duration
        if results:
            log_data['results'] = results
        
        self.logger.info(f"Completed operation: {operation}", extra=log_data)
        self.clear_context()
    
    def log_api_call(self, api_name: str, endpoint: str, method: str = "GET", **params):
        """Log API calls with structured data"""
        self.logger.debug(
            f"API call: {api_name}",
            extra={
                'api_call': True,
                'api_name': api_name,
                'endpoint': endpoint,
                'method': method,
                'parameters': params
            }
        )
    
    def log_api_response(self, api_name: str, status_code: int, response_time: float, **metadata):
        """Log API responses with performance data"""
        self.logger.info(
            f"API response: {api_name} ({status_code})",
            extra={
                'api_response': True,
                'api_name': api_name,
                'status_code': status_code,
                'response_time_ms': response_time * 1000,
                'metadata': metadata
            }
        )
    
    def log_error(self, error: Exception, operation: str = None, **context):
        """Log errors with full context and traceback"""
        error_context = {
            'error_type': type(error).__name__,
            'error_message': str(error),
        }
        
        if operation:
            error_context['operation'] = operation
        
        error_context.update(context)
        
        self.logger.error(
            f"Error in {operation or 'unknown operation'}: {error}",
            extra=error_context,
            exc_info=True
        )
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """Log performance metrics"""
        self.logger.info(
            f"Performance: {operation} completed in {duration:.2f}s",
            extra={
                'performance': True,
                'operation': operation,
                'duration_seconds': duration,
                'metrics': metrics
            }
        )
    
    def log_validation_error(self, error: str, field: str = None, value: Any = None):
        """Log validation errors"""
        self.logger.warning(
            f"Validation error: {error}",
            extra={
                'validation_error': True,
                'error_message': error,
                'field': field,
                'value': str(value) if value is not None else None
            }
        )
    
    def get_logger(self):
        """Get the underlying logger instance"""
        return self.logger


# Global logger instance
_global_logger = ResearchAssistantLogger()

def setup_logging(log_level: str = None, structured: bool = True):
    """Setup logging with Rich formatting and structured output"""
    return _global_logger.setup_logging(log_level, structured)

def get_logger(name: str = None):
    """Get a logger instance"""
    if name:
        return logging.getLogger(name)
    return _global_logger.get_logger()

def set_context(**kwargs):
    """Set context for logging"""
    _global_logger.set_context(**kwargs)

def clear_context():
    """Clear logging context"""
    _global_logger.clear_context()

def log_operation(operation: str, **context):
    """Log operation start"""
    _global_logger.log_operation(operation, **context)

def log_operation_complete(operation: str, duration: float = None, **results):
    """Log operation completion"""
    _global_logger.log_operation_complete(operation, duration, **results)

def log_api_call(api_name: str, endpoint: str, method: str = "GET", **params):
    """Log API call"""
    _global_logger.log_api_call(api_name, endpoint, method, **params)

def log_api_response(api_name: str, status_code: int, response_time: float, **metadata):
    """Log API response"""
    _global_logger.log_api_response(api_name, status_code, response_time, **metadata)

def log_error(error: Exception, operation: str = None, **context):
    """Log error with context"""
    _global_logger.log_error(error, operation, **context)

def log_performance(operation: str, duration: float, **metrics):
    """Log performance metrics"""
    _global_logger.log_performance(operation, duration, **metrics)

# Initialize logger
logger = setup_logging()