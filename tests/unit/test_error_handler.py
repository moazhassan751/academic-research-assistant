"""
Tests for enhanced error handling system
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch
from src.utils.error_handler import (
    ErrorHandler,
    ErrorType,
    ErrorSeverity,
    ErrorContext,
    ResearchAssistantError,
    APIError,
    DatabaseError,
    ValidationError,
    NetworkError,
    ErrorRecoveryManager,
    handle_errors,
    handle_async_errors,
    safe_execute,
    safe_execute_async
)


class TestErrorContext:
    """Test error context functionality"""
    
    def test_error_context_creation(self):
        """Test basic error context creation"""
        context = ErrorContext(
            error_type=ErrorType.API_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Test error message",
            details={'key': 'value'},
            user_message="User-friendly error",
            recovery_suggestions=["Try again", "Check connection"]
        )
        
        assert context.error_type == ErrorType.API_ERROR
        assert context.severity == ErrorSeverity.HIGH
        assert context.message == "Test error message"
        assert context.details == {'key': 'value'}
        assert context.user_message == "User-friendly error"
        assert len(context.recovery_suggestions) == 2
        assert context.timestamp is not None
    
    def test_error_context_to_dict(self):
        """Test error context serialization"""
        context = ErrorContext(
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Validation failed"
        )
        
        result = context.to_dict()
        
        assert result['error_type'] == 'validation_error'
        assert result['severity'] == 'medium'
        assert result['message'] == 'Validation failed'
        assert 'timestamp' in result
    
    def test_error_context_to_json(self):
        """Test JSON serialization"""
        context = ErrorContext(
            error_type=ErrorType.DATABASE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Database connection failed"
        )
        
        json_str = context.to_json()
        assert '"error_type": "database_error"' in json_str
        assert '"severity": "critical"' in json_str


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_research_assistant_error(self):
        """Test base ResearchAssistantError"""
        error = ResearchAssistantError(
            "Test error",
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            details={'url': 'https://api.example.com'},
            user_message="Network connection failed",
            recovery_suggestions=["Check internet", "Try again"]
        )
        
        assert str(error) == "Test error"
        assert error.error_context.error_type == ErrorType.NETWORK_ERROR
        assert error.error_context.severity == ErrorSeverity.HIGH
        assert error.error_context.details['url'] == 'https://api.example.com'
        assert error.error_context.user_message == "Network connection failed"
        assert len(error.error_context.recovery_suggestions) == 2
    
    def test_api_error(self):
        """Test APIError specific fields"""
        error = APIError(
            "API request failed",
            api_name="OpenAlex",
            status_code=429,
            response_data={'error': 'Rate limit exceeded'}
        )
        
        assert error.error_context.error_type == ErrorType.API_ERROR
        assert error.error_context.severity == ErrorSeverity.HIGH
        assert error.error_context.details['api_name'] == "OpenAlex"
        assert error.error_context.details['status_code'] == 429
        assert error.error_context.details['response_data']['error'] == 'Rate limit exceeded'
        assert "API request failed: API request failed" in error.error_context.user_message
    
    def test_database_error(self):
        """Test DatabaseError specific fields"""
        error = DatabaseError(
            "INSERT failed",
            operation="insert",
            table="papers"
        )
        
        assert error.error_context.error_type == ErrorType.DATABASE_ERROR
        assert error.error_context.details['operation'] == "insert"
        assert error.error_context.details['table'] == "papers"
    
    def test_validation_error(self):
        """Test ValidationError specific fields"""
        error = ValidationError(
            "Invalid email format",
            field="email",
            value="not-an-email"
        )
        
        assert error.error_context.error_type == ErrorType.VALIDATION_ERROR
        assert error.error_context.severity == ErrorSeverity.MEDIUM
        assert error.error_context.details['field'] == "email"
        assert error.error_context.details['value'] == "not-an-email"
    
    def test_network_error(self):
        """Test NetworkError specific fields"""
        error = NetworkError(
            "Connection timeout",
            url="https://api.example.com"
        )
        
        assert error.error_context.error_type == ErrorType.NETWORK_ERROR
        assert error.error_context.details['url'] == "https://api.example.com"


class TestErrorHandler:
    """Test error handler functionality"""
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler for testing"""
        return ErrorHandler(log_to_file=False)
    
    def test_error_handler_initialization(self, error_handler):
        """Test error handler initialization"""
        assert error_handler.error_counts == {}
        assert error_handler.recent_errors == []
        assert error_handler.max_recent_errors == 100
    
    def test_handle_custom_error(self, error_handler):
        """Test handling of custom ResearchAssistantError"""
        error = APIError("Test API error", api_name="TestAPI")
        
        context = error_handler.handle_error(error)
        
        assert context.error_type == ErrorType.API_ERROR
        assert context.severity == ErrorSeverity.HIGH
        assert "Test API error" in context.message
    
    def test_handle_generic_error(self, error_handler):
        """Test handling of generic exceptions"""
        error = ValueError("Invalid value")
        
        context = error_handler.handle_error(error, {'test': 'context'})
        
        assert context.error_type == ErrorType.VALIDATION_ERROR  # Should classify ValueError
        assert context.message == "Invalid value"
        assert context.details == {'test': 'context'}
        assert context.user_message is not None
        assert len(context.recovery_suggestions) > 0
    
    def test_error_classification(self, error_handler):
        """Test error classification logic"""
        # Test different error types
        test_cases = [
            (ConnectionError("Connection failed"), ErrorType.NETWORK_ERROR),
            (TimeoutError("Operation timed out"), ErrorType.TIMEOUT_ERROR),
            (ValueError("Invalid JSON"), ErrorType.PARSING_ERROR),
            (FileNotFoundError("File not found"), ErrorType.FILE_ERROR),
        ]
        
        for exception, expected_type in test_cases:
            context = error_handler._create_error_context(exception)
            assert context.error_type == expected_type
    
    def test_severity_determination(self, error_handler):
        """Test error severity determination"""
        # Critical error
        context = error_handler._create_error_context(Exception("Database error"))
        context.error_type = ErrorType.DATABASE_ERROR
        severity = error_handler._determine_severity(Exception(), ErrorType.DATABASE_ERROR)
        assert severity == ErrorSeverity.CRITICAL
        
        # High severity error
        severity = error_handler._determine_severity(Exception(), ErrorType.API_ERROR)
        assert severity == ErrorSeverity.HIGH
        
        # Medium severity error
        severity = error_handler._determine_severity(Exception(), ErrorType.VALIDATION_ERROR)
        assert severity == ErrorSeverity.MEDIUM
    
    def test_error_tracking(self, error_handler):
        """Test error statistics tracking"""
        # Handle multiple errors
        error1 = APIError("API Error 1")
        error2 = ValidationError("Validation Error")
        error3 = APIError("API Error 2")
        
        error_handler.handle_error(error1)
        error_handler.handle_error(error2)
        error_handler.handle_error(error3)
        
        stats = error_handler.get_error_statistics()
        assert stats['total_errors'] == 3
        assert 'api_error:high' in stats['error_counts']
        assert 'validation_error:medium' in stats['error_counts']
        assert stats['error_counts']['api_error:high'] == 2
        assert stats['error_counts']['validation_error:medium'] == 1
    
    def test_recent_errors_limit(self, error_handler):
        """Test recent errors list limitation"""
        error_handler.max_recent_errors = 3
        
        # Add more errors than limit
        for i in range(5):
            error = APIError(f"Error {i}")
            error_handler.handle_error(error)
        
        # Should only keep last 3 errors
        assert len(error_handler.recent_errors) == 3
        
        # Check that we have the most recent errors
        recent = error_handler.get_recent_errors()
        assert "Error 4" in recent[0].message  # Most recent
        assert "Error 2" in recent[2].message  # Oldest kept
    
    def test_clear_error_history(self, error_handler):
        """Test clearing error history"""
        # Add some errors
        error_handler.handle_error(APIError("Test error"))
        
        assert len(error_handler.recent_errors) > 0
        assert error_handler.error_counts
        
        # Clear history
        error_handler.clear_error_history()
        
        assert len(error_handler.recent_errors) == 0
        assert not error_handler.error_counts


class TestErrorDecorators:
    """Test error handling decorators"""
    
    def test_handle_errors_decorator_success(self):
        """Test decorator with successful function"""
        
        @handle_errors()
        def successful_function(x, y):
            return x + y
        
        result = successful_function(2, 3)
        assert result == 5
    
    def test_handle_errors_decorator_with_error(self):
        """Test decorator with error"""
        
        @handle_errors(error_type=ErrorType.API_ERROR, reraise=False, default_return="ERROR")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "ERROR"
    
    def test_handle_errors_decorator_reraise(self):
        """Test decorator with reraise=True"""
        
        @handle_errors(reraise=True)
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ResearchAssistantError):
            failing_function()
    
    @pytest.mark.asyncio
    async def test_handle_async_errors_decorator(self):
        """Test async error decorator"""
        
        @handle_async_errors(error_type=ErrorType.NETWORK_ERROR, reraise=False, default_return=None)
        async def async_failing_function():
            raise ConnectionError("Network error")
        
        result = await async_failing_function()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_async_errors_success(self):
        """Test async decorator with successful function"""
        
        @handle_async_errors()
        async def async_successful_function(x):
            await asyncio.sleep(0.01)  # Small delay to make it actually async
            return x * 2
        
        result = await async_successful_function(5)
        assert result == 10


class TestSafeExecution:
    """Test safe execution functions"""
    
    def test_safe_execute_success(self):
        """Test safe execution with successful function"""
        
        def successful_func(a, b):
            return a + b
        
        success, result, error_context = safe_execute(successful_func, 2, 3)
        
        assert success is True
        assert result == 5
        assert error_context is None
    
    def test_safe_execute_failure(self):
        """Test safe execution with failing function"""
        
        def failing_func():
            raise ValueError("Test error")
        
        success, result, error_context = safe_execute(failing_func)
        
        assert success is False
        assert result is None
        assert error_context is not None
        assert error_context.error_type == ErrorType.VALIDATION_ERROR
        assert "Test error" in error_context.message
    
    @pytest.mark.asyncio
    async def test_safe_execute_async_success(self):
        """Test async safe execution with successful function"""
        
        async def async_successful_func(x):
            await asyncio.sleep(0.01)
            return x * 2
        
        success, result, error_context = await safe_execute_async(async_successful_func, 5)
        
        assert success is True
        assert result == 10
        assert error_context is None
    
    @pytest.mark.asyncio
    async def test_safe_execute_async_failure(self):
        """Test async safe execution with failing function"""
        
        async def async_failing_func():
            await asyncio.sleep(0.01)
            raise ConnectionError("Network error")
        
        success, result, error_context = await safe_execute_async(async_failing_func)
        
        assert success is False
        assert result is None
        assert error_context is not None
        assert error_context.error_type == ErrorType.NETWORK_ERROR


class TestErrorRecoveryManager:
    """Test error recovery functionality"""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create recovery manager for testing"""
        return ErrorRecoveryManager()
    
    @pytest.mark.asyncio
    async def test_api_error_recovery(self, recovery_manager):
        """Test API error recovery"""
        error_context = ErrorContext(
            error_type=ErrorType.API_ERROR,
            severity=ErrorSeverity.HIGH,
            message="API timeout"
        )
        
        # Mock function to retry
        mock_func = Mock(return_value="success")
        
        success, result = await recovery_manager.attempt_recovery(
            error_context, mock_func
        )
        
        assert success is True
        assert result == "success"
        mock_func.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_network_error_recovery(self, recovery_manager):
        """Test network error recovery"""
        error_context = ErrorContext(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Connection failed"
        )
        
        async def async_func():
            return "recovered"
        
        success, result = await recovery_manager.attempt_recovery(
            error_context, async_func
        )
        
        assert success is True
        assert result == "recovered"
    
    @pytest.mark.asyncio
    async def test_no_recovery_strategy(self, recovery_manager):
        """Test error type with no recovery strategy"""
        error_context = ErrorContext(
            error_type=ErrorType.UNKNOWN_ERROR,
            severity=ErrorSeverity.LOW,
            message="Unknown error"
        )
        
        mock_func = Mock()
        
        success, result = await recovery_manager.attempt_recovery(
            error_context, mock_func
        )
        
        assert success is False
        assert result is None
        mock_func.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_recovery_fails_retry(self, recovery_manager):
        """Test recovery success but retry still fails"""
        error_context = ErrorContext(
            error_type=ErrorType.RATE_LIMIT_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Rate limit exceeded"
        )
        
        def failing_func():
            raise Exception("Still failing")
        
        # Mock the recovery strategy to return True but function still fails
        with patch.object(recovery_manager, '_recover_rate_limit_error', return_value=True):
            success, result = await recovery_manager.attempt_recovery(
                error_context, failing_func
            )
        
        assert success is False
        assert result is None


class TestErrorIntegration:
    """Integration tests for error handling system"""
    
    @pytest.mark.asyncio
    async def test_full_error_flow(self):
        """Test complete error handling flow"""
        
        # Create a function that fails then succeeds
        call_count = 0
        
        @handle_async_errors(reraise=False, default_return="fallback")
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APIError("First attempt failed", api_name="TestAPI")
            return "success"
        
        # First call should return fallback due to error
        result1 = await flaky_function()
        assert result1 == "fallback"
        
        # Second call should succeed
        result2 = await flaky_function()
        assert result2 == "success"
    
    def test_error_statistics_integration(self):
        """Test error statistics across multiple operations"""
        from src.utils.error_handler import error_handler
        
        # Clear any existing stats
        error_handler.clear_error_history()
        
        # Generate various errors
        errors = [
            APIError("API Error 1"),
            APIError("API Error 2"),
            ValidationError("Validation Error"),
            NetworkError("Network Error")
        ]
        
        for error in errors:
            error_handler.handle_error(error)
        
        stats = error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 4
        assert len(stats['error_types']) >= 3  # At least 3 different error types
        assert 'api_error' in stats['most_common_error']
    
    def test_logging_integration(self):
        """Test that errors are properly logged"""
        
        with patch('src.utils.error_handler.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Create new error handler to trigger logging setup
            handler = ErrorHandler(log_to_file=False)
            
            # Handle an error
            error = APIError("Test logging")
            handler.handle_error(error)
            
            # Verify logger was configured
            mock_get_logger.assert_called()
            
            # Note: We can't easily test the actual logging calls without 
            # more complex mocking, but we can verify the setup
