"""
Production Error Handler and Validation System
Comprehensive error handling for production deployment
"""

import traceback
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional
import streamlit as st
from datetime import datetime

class ProductionErrorHandler:
    """Production-grade error handler for Streamlit applications"""
    
    def __init__(self):
        self.setup_logging()
        self.error_count = 0
        self.last_error_time = None
    
    def setup_logging(self):
        """Setup production logging"""
        # Ensure logs directory exists
        import os
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/production_errors.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> tuple[bool, Any]:
        """Safely execute a function with comprehensive error handling"""
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            self.log_error(e, func.__name__)
            return False, None
    
    def log_error(self, error: Exception, context: str = "Unknown"):
        """Log error with context and stack trace"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': self.last_error_time.isoformat(),
            'stack_trace': traceback.format_exc()
        }
        
        self.logger.error(f"Production Error in {context}: {error_details}")
        return error_details
    
    def display_user_friendly_error(self, error_type: str = "general"):
        """Display user-friendly error messages"""
        error_messages = {
            'network': {
                'title': '🌐 Network Connection Issue',
                'message': 'Please check your internet connection and try again.',
                'suggestions': [
                    'Verify your internet connection',
                    'Check if the academic databases are accessible',
                    'Try refreshing the page'
                ]
            },
            'api': {
                'title': '🔑 API Configuration Issue',
                'message': 'There seems to be an issue with the API configuration.',
                'suggestions': [
                    'Check API key configuration',
                    'Verify API rate limits',
                    'Contact system administrator'
                ]
            },
            'data': {
                'title': '📊 Data Processing Issue',
                'message': 'Unable to process the requested data.',
                'suggestions': [
                    'Try with different search terms',
                    'Reduce the scope of your query',
                    'Check data format and inputs'
                ]
            },
            'general': {
                'title': '⚠️ Unexpected Issue',
                'message': 'An unexpected error occurred. The system is still functional.',
                'suggestions': [
                    'Try refreshing the page',
                    'Clear your browser cache',
                    'Try a different browser'
                ]
            }
        }
        
        error_info = error_messages.get(error_type, error_messages['general'])
        
        st.error(f"**{error_info['title']}**\n\n{error_info['message']}", icon="🚨")
        
        with st.expander("🔧 Troubleshooting Steps"):
            for suggestion in error_info['suggestions']:
                st.write(f"• {suggestion}")
    
    def validate_session_state(self) -> bool:
        """Validate session state integrity"""
        required_keys = ['research_crew', 'qa_agent', 'research_results']
        
        for key in required_keys:
            if key not in st.session_state:
                if key in ['research_crew', 'qa_agent']:
                    # These are optional, show warning
                    st.warning(f"⚠️ {key} not initialized. Some features may be limited.", icon="🔧")
                    return False
        
        return True
    
    def safe_streamlit_component(self, component_func: Callable, fallback_content: str = None):
        """Safely render Streamlit components with fallback"""
        try:
            return component_func()
        except Exception as e:
            self.log_error(e, f"Streamlit Component: {component_func.__name__}")
            if fallback_content:
                st.markdown(fallback_content)
            else:
                st.info("⚠️ Component temporarily unavailable", icon="🔧")
            return None

# Global error handler instance
production_handler = ProductionErrorHandler()

def production_safe(error_type: str = "general", fallback_value: Any = None):
    """Decorator for production-safe function execution"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            success, result = production_handler.safe_execute(func, *args, **kwargs)
            if success:
                return result
            else:
                production_handler.display_user_friendly_error(error_type)
                return fallback_value
        return wrapper
    return decorator

def validate_inputs(**validators) -> bool:
    """Validate inputs with custom validators"""
    for field_name, (value, validator_func, error_message) in validators.items():
        if not validator_func(value):
            st.error(f"❌ **{field_name}**: {error_message}", icon="🚨")
            return False
    return True

def safe_data_access(data: Dict, key_path: str, default: Any = None):
    """Safely access nested dictionary data"""
    try:
        keys = key_path.split('.')
        result = data
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError):
        return default

# Production configuration validation
def validate_production_config():
    """Validate production configuration"""
    config_checks = {
        'streamlit_version': True,  # Add actual version checks
        'python_version': True,     # Add actual version checks
        'dependencies': True,       # Add dependency checks
        'environment': True         # Add environment checks
    }
    
    issues = []
    for check, status in config_checks.items():
        if not status:
            issues.append(check)
    
    if issues:
        st.error(f"❌ Production Configuration Issues: {', '.join(issues)}", icon="🚨")
        return False
    
    return True

if __name__ == "__main__":
    # Test the error handler
    print("🧪 Testing Production Error Handler...")
    
    # Test safe execution
    def test_function():
        return "Success"
    
    def failing_function():
        raise ValueError("Test error")
    
    success, result = production_handler.safe_execute(test_function)
    print(f"✅ Safe execution test: {success}, {result}")
    
    success, result = production_handler.safe_execute(failing_function)
    print(f"❌ Error handling test: {success}, {result}")
    
    print("🎯 Production Error Handler Ready!")
