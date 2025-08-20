"""
Professional Error Handler for Dashboard
Ensures graceful error handling and user-friendly messages
"""
import streamlit as st
import traceback
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable

class ProfessionalErrorHandler:
    def __init__(self):
        self.error_count = 0
        self.error_log = []
        
    def handle_error(self, error: Exception, context: str = "", user_friendly: bool = True):
        """Handle errors professionally with logging and user feedback"""
        self.error_count += 1
        error_details = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'type': type(error).__name__,
            'context': context,
            'traceback': traceback.format_exc()
        }
        self.error_log.append(error_details)
        
        # Log the error
        logging.error(f"Dashboard Error in {context}: {error}")
        
        if user_friendly:
            # Show user-friendly error message
            self.show_user_error(error, context)
        else:
            # Show technical error for debugging
            st.error(f"Technical Error in {context}: {str(error)}")
            with st.expander("🐛 Technical Details"):
                st.code(traceback.format_exc())
    
    def show_user_error(self, error: Exception, context: str):
        """Show user-friendly error messages"""
        error_type = type(error).__name__
        
        # Map technical errors to user-friendly messages
        user_messages = {
            'ConnectionError': "🌐 Unable to connect to the research database. Please check your internet connection.",
            'TimeoutError': "⏱️ The operation took too long. Please try again with fewer papers or a simpler query.",
            'PermissionError': "🔒 Access denied. Please check file permissions or contact your administrator.",
            'FileNotFoundError': "📁 Required file not found. The system may need to be reconfigured.",
            'KeyError': "🔑 Missing required information. Please check your input and try again.",
            'ValueError': "📝 Invalid input provided. Please check your parameters and try again.",
            'ImportError': "📦 Required system component not available. Please contact technical support.",
            'DatabaseError': "🗃️ Database operation failed. Please try again or contact support.",
            'APIError': "🔌 External service unavailable. Please try again later.",
        }
        
        message = user_messages.get(error_type, f"⚠️ An unexpected error occurred in {context}. Please try again.")
        
        st.error(message, icon="🚨")
        
        # Provide helpful suggestions
        suggestions = {
            'ConnectionError': [
                "Check your internet connection",
                "Verify VPN settings if using one",
                "Try refreshing the page"
            ],
            'TimeoutError': [
                "Reduce the number of papers to analyze",
                "Try a more specific search query",
                "Check system load and try again later"
            ],
            'ValueError': [
                "Check your input format",
                "Ensure all required fields are filled",
                "Try using example values"
            ],
        }
        
        if error_type in suggestions:
            with st.expander("💡 Troubleshooting Tips"):
                for tip in suggestions[error_type]:
                    st.write(f"• {tip}")
    
    def with_error_handling(self, context: str = "", user_friendly: bool = True):
        """Decorator for automatic error handling"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.handle_error(e, context or func.__name__, user_friendly)
                    return None
            return wrapper
        return decorator
    
    def get_error_summary(self) -> dict:
        """Get summary of errors for monitoring"""
        return {
            'total_errors': self.error_count,
            'recent_errors': len([e for e in self.error_log if 
                                datetime.fromisoformat(e['timestamp']) > 
                                datetime.now().replace(hour=0, minute=0, second=0)]),
            'error_types': list(set([e['type'] for e in self.error_log])),
            'last_error': self.error_log[-1] if self.error_log else None
        }

# Global error handler instance
error_handler = ProfessionalErrorHandler()

def safe_execute(func: Callable, context: str = "", default_return=None, show_errors: bool = True):
    """Safely execute a function with error handling"""
    try:
        return func()
    except Exception as e:
        if show_errors:
            error_handler.handle_error(e, context)
        else:
            logging.error(f"Silent error in {context}: {e}")
        return default_return

def validate_inputs(**kwargs):
    """Validate user inputs before processing"""
    errors = []
    
    for name, value in kwargs.items():
        if name == 'research_topic' and (not value or len(value.strip()) < 3):
            errors.append("Research topic must be at least 3 characters long")
        
        if name == 'max_papers' and (value < 1 or value > 1000):
            errors.append("Number of papers must be between 1 and 1000")
        
        if name == 'question' and (not value or len(value.strip()) < 5):
            errors.append("Question must be at least 5 characters long")
    
    if errors:
        for error in errors:
            st.error(f"❌ {error}")
        return False
    
    return True

def show_system_health():
    """Show system health status"""
    error_summary = error_handler.get_error_summary()
    
    if error_summary['total_errors'] == 0:
        st.success("🟢 System running smoothly - No errors detected")
    elif error_summary['recent_errors'] == 0:
        st.info(f"🟡 System stable - {error_summary['total_errors']} historical errors, none recent")
    else:
        st.warning(f"🟠 {error_summary['recent_errors']} recent errors - System functional but monitoring needed")
        
        if error_summary['recent_errors'] > 5:
            st.error("🔴 High error rate detected - Please contact technical support")
