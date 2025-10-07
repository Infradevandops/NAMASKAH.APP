#!/usr/bin/env python3
"""
Unit tests for Error Handling System
Tests exceptions, retry logic, circuit breakers, and comprehensive error handling
"""
import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.circuit_breaker import (CircuitBreaker, CircuitBreakerConfig,
                                  CircuitBreakerError, CircuitState,
                                  circuit_manager)
from core.error_handler import (ErrorHandlerConfig, ErrorReporter,
                                ServiceErrorHandler, get_error_handling_health,
                                with_error_handling, handle_errors)
from core.exceptions import (BaseServiceException, ErrorCategory,
                             ErrorSeverity, TextVerifiedAuthenticationError,
                             TextVerifiedException, TwilioException,
                             TwilioRateLimitError, map_textverified_error,
                             map_twilio_error)
from core.retry_handler import (RetryConfig, RetryHandler, RetryStrategy,
                                textverified_retry_decorator,
                                twilio_retry_decorator)


class TestExceptions:
    """Test custom exception classes"""

    def test_base_service_exception(self):
        """Test base service exception"""
        error = BaseServiceException(
            "Test error",
            error_code="TEST_001",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.EXTERNAL_API,
            is_retryable=True,
            retry_after=60,
        )

        assert error.message == "Test error"
        assert error.error_code == "TEST_001"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.EXTERNAL_API
        assert error.is_retryable is True
        assert error.retry_after == 60

        error_dict = error.to_dict()
        assert error_dict["error_type"] == "BaseServiceException"
        assert error_dict["message"] == "Test error"
        assert error_dict["severity"] == "high"

    def test_textverified_authentication_error(self):
        """Test TextVerified authentication error"""
        error = TextVerifiedAuthenticationError()

        assert error.error_code == "TV_AUTH_FAILED"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.is_retryable is False

    def test_twilio_rate_limit_error(self):
        """Test Twilio rate limit error"""
        error = TwilioRateLimitError(retry_after=300)

        assert error.error_code == "TW_RATE_LIMIT"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.RATE_LIMIT
        assert error.is_retryable is True
        assert error.retry_after == 300

    def test_error_mapping_textverified(self):
        """Test TextVerified error mapping"""
        error = map_textverified_error("401", "Authentication failed")
        assert isinstance(error, TextVerifiedAuthenticationError)

        error = map_textverified_error("429", "Rate limit exceeded")
        assert error.error_code == "TV_RATE_LIMIT"

    def test_error_mapping_twilio(self):
        """Test Twilio error mapping"""
        error = map_twilio_error("20429", "Rate limit exceeded")
        assert isinstance(error, TwilioRateLimitError)

        error = map_twilio_error("21211", "Invalid phone number")
        assert "Invalid phone number" in str(error)


class TestRetryHandler:
    """Test retry handler functionality"""

    @pytest.fixture
    def retry_config(self):
        """Create test retry configuration"""
        return RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=False,  # Disable jitter for predictable tests
        )

    @pytest.fixture
    def retry_handler(self, retry_config):
        """Create retry handler instance"""
        return RetryHandler(retry_config)

    @pytest.mark.asyncio
    async def test_successful_execution(self, retry_handler):
        """Test successful function execution"""
        mock_func = AsyncMock(return_value="success")

        result = await retry_handler.execute_with_retry(
            mock_func, "arg1", kwarg1="value1"
        )

        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")

    @pytest.mark.asyncio
    async def test_retry_on_retryable_error(self, retry_handler):
        """Test retry behavior on retryable errors"""
        mock_func = AsyncMock(
            side_effect=[
                ConnectionError("Connection failed"),
                ConnectionError("Connection failed"),
                "success",
            ]
        )

        result = await retry_handler.execute_with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self, retry_handler):
        """Test no retry on non-retryable errors"""
        mock_func = AsyncMock(side_effect=ValueError("Invalid input"))

        with pytest.raises(ValueError):
            await retry_handler.execute_with_retry(mock_func)

        mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self, retry_handler):
        """Test behavior when max attempts are exceeded"""
        mock_func = AsyncMock(side_effect=ConnectionError("Always fails"))

        with pytest.raises(ConnectionError):
            await retry_handler.execute_with_retry(mock_func)

        assert mock_func.call_count == 3  # max_attempts

    @pytest.mark.asyncio
    async def test_exponential_backoff_delay(self, retry_handler):
        """Test exponential backoff delay calculation"""
        delay1 = retry_handler.calculate_delay(1)
        delay2 = retry_handler.calculate_delay(2)
        delay3 = retry_handler.calculate_delay(3)

        assert delay1 == 0.1  # base_delay * 2^0
        assert delay2 == 0.2  # base_delay * 2^1
        assert delay3 == 0.4  # base_delay * 2^2

    @pytest.mark.asyncio
    async def test_retry_decorator(self):
        """Test retry decorator functionality"""
        call_count = 0

        @textverified_retry_decorator
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await failing_function()

        assert result == "success"
        assert call_count == 3


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    @pytest.fixture
    def circuit_config(self):
        """Create test circuit breaker configuration"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1.0,
            success_threshold=2,
            timeout=0.5,
            minimum_requests=2,
        )

    @pytest.fixture
    def circuit_breaker(self, circuit_config):
        """Create circuit breaker instance"""
        return CircuitBreaker("test_service", circuit_config)

    @pytest.mark.asyncio
    async def test_successful_calls_keep_circuit_closed(self, circuit_breaker):
        """Test that successful calls keep circuit closed"""
        mock_func = AsyncMock(return_value="success")

        for _ in range(5):
            result = await circuit_breaker.call(mock_func)
            assert result == "success"

        assert circuit_breaker.get_state() == CircuitState.CLOSED
        assert mock_func.call_count == 5

    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self, circuit_breaker):
        """Test that circuit opens after threshold failures"""
        mock_func = AsyncMock(side_effect=ConnectionError("Service down"))

        # First few failures should go through
        for i in range(3):
            with pytest.raises(ConnectionError):
                await circuit_breaker.call(mock_func)

        # Circuit should now be open
        assert circuit_breaker.get_state() == CircuitState.OPEN

        # Next call should fail fast
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.call(mock_func)

    @pytest.mark.asyncio
    async def test_circuit_recovery_to_half_open(self, circuit_breaker):
        """Test circuit recovery to half-open state"""
        mock_func = AsyncMock(side_effect=ConnectionError("Service down"))

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await circuit_breaker.call(mock_func)

        assert circuit_breaker.get_state() == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next call should transition to half-open
        mock_func.side_effect = None
        mock_func.return_value = "success"

        result = await circuit_breaker.call(mock_func)
        assert result == "success"
        assert circuit_breaker.get_state() == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_closes_after_successful_calls(self, circuit_breaker):
        """Test circuit closes after successful calls in half-open state"""
        # Manually set to half-open state
        circuit_breaker._half_open_circuit()

        mock_func = AsyncMock(return_value="success")

        # Make successful calls to close circuit
        for _ in range(2):  # success_threshold = 2
            result = await circuit_breaker.call(mock_func)
            assert result == "success"

        assert circuit_breaker.get_state() == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_timeout_handling(self, circuit_breaker):
        """Test timeout handling in circuit breaker"""

        async def slow_function():
            await asyncio.sleep(1.0)  # Longer than timeout (0.5s)
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await circuit_breaker.call(slow_function)

    def test_circuit_breaker_stats(self, circuit_breaker):
        """Test circuit breaker statistics"""
        stats = circuit_breaker.get_stats()

        assert "state" in stats
        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert stats["state"] == "closed"

    def test_manual_reset(self, circuit_breaker):
        """Test manual circuit breaker reset"""
        # Force open the circuit
        circuit_breaker.force_open()
        assert circuit_breaker.get_state() == CircuitState.OPEN

        # Reset the circuit
        circuit_breaker.reset()
        assert circuit_breaker.get_state() == CircuitState.CLOSED


class TestErrorReporter:
    """Test error reporter functionality"""

    @pytest.fixture
    def error_reporter(self):
        """Create error reporter instance"""
        return ErrorReporter()

    @pytest.mark.asyncio
    async def test_error_reporting(self, error_reporter):
        """Test basic error reporting"""
        error = ValueError("Test error")

        await error_reporter.report_error(
            error, "test_service", "test_operation", {"key": "value"}
        )

        stats = error_reporter.get_error_stats()
        assert stats["total_errors"] == 1
        assert "test_service.test_operation.ValueError" in stats["error_counts"]
        assert len(stats["recent_errors"]) == 1

    @pytest.mark.asyncio
    async def test_error_count_accumulation(self, error_reporter):
        """Test error count accumulation"""
        error = ValueError("Test error")

        # Report same error multiple times
        for _ in range(3):
            await error_reporter.report_error(error, "test_service", "test_operation")

        stats = error_reporter.get_error_stats()
        assert stats["total_errors"] == 3
        assert stats["error_counts"]["test_service.test_operation.ValueError"] == 3


class TestServiceErrorHandler:
    """Test service error handler functionality"""

    @pytest.fixture
    def error_config(self):
        """Create error handler configuration"""
        return ErrorHandlerConfig(
            service_name="test_service",
            enable_retry=True,
            enable_circuit_breaker=True,
            enable_error_reporting=True,
        )

    @pytest.fixture
    def error_handler(self, error_config):
        """Create service error handler"""
        return ServiceErrorHandler(error_config)

    @pytest.mark.asyncio
    async def test_successful_execution_with_error_handling(self, error_handler):
        """Test successful execution with error handling"""
        mock_func = AsyncMock(return_value="success")

        result = await error_handler.execute_with_error_handling(
            mock_func, "test_operation", "arg1", kwarg1="value1"
        )

        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")

    @pytest.mark.asyncio
    async def test_error_handling_with_retry_and_circuit_breaker(self, error_handler):
        """Test error handling with both retry and circuit breaker"""
        call_count = 0

        async def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await error_handler.execute_with_error_handling(
            failing_then_succeeding, "test_operation"
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_error_mapping(self, error_handler):
        """Test error mapping functionality"""

        # Mock error mapping function
        def mock_error_mapper(error):
            if isinstance(error, ValueError):
                return TextVerifiedException("Mapped error")
            return error

        error_handler.config.error_mapping_func = mock_error_mapper

        mock_func = AsyncMock(side_effect=ValueError("Original error"))

        with pytest.raises(TextVerifiedException) as exc_info:
            await error_handler.execute_with_error_handling(mock_func, "test_operation")

        assert "Mapped error" in str(exc_info.value)

    def test_error_handler_stats(self, error_handler):
        """Test error handler statistics"""
        stats = error_handler.get_stats()

        assert "service_name" in stats
        assert "error_stats" in stats
        assert "retry_stats" in stats
        assert "circuit_breaker_stats" in stats
        assert stats["service_name"] == "test_service"


class TestErrorHandlingDecorators:
    """Test error handling decorators"""

    @pytest.mark.asyncio
    async def test_with_error_handling_decorator(self):
        """Test with_error_handling decorator"""
        call_count = 0

        @with_error_handling("test_service", "test_operation")
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await test_function()

        assert result == "success"
        assert call_count == 2




class TestHandleErrorsDecorator:
    """Test handle_errors decorator"""

    @pytest.mark.asyncio
    async def test_handle_errors_success(self):
        """Test handle_errors decorator on successful function"""
        @handle_errors
        async def successful_function():
            return "success"

        result = await successful_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_handle_errors_with_exception(self):
        """Test handle_errors decorator with exception"""
        @handle_errors
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()

    @pytest.mark.asyncio
    async def test_handle_errors_with_retryable_error(self):
        """Test handle_errors decorator with retryable error"""
        call_count = 0

        @handle_errors
        async def retryable_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await retryable_function()
        assert result == "success"
        assert call_count == 3  # Should have retried


class TestErrorHandlingIntegration:
    """Integration tests for complete error handling system"""

    @pytest.mark.asyncio
    async def test_complete_error_handling_workflow(self):
        """Test complete error handling workflow"""
        # Simulate a service that fails initially then recovers
        call_count = 0

        @with_error_handling(
            "integration_test", enable_retry=True, enable_circuit_breaker=True
        )
        async def unreliable_service():
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                raise ConnectionError("Service temporarily unavailable")
            elif call_count <= 5:
                return f"success_{call_count}"
            else:
                raise ConnectionError("Service down again")

        # First call should succeed after retries
        result1 = await unreliable_service()
        assert result1 == "success_3"

        # Next calls should succeed immediately
        result2 = await unreliable_service()
        assert result2 == "success_4"

        result3 = await unreliable_service()
        assert result3 == "success_5"

        # This should fail and potentially open circuit after multiple attempts
        with pytest.raises(ConnectionError):
            await unreliable_service()

    @pytest.mark.asyncio
    async def test_health_check_functionality(self):
        """Test error handling health check"""
        health = await get_error_handling_health()

        assert "healthy" in health
        assert "unhealthy_services" in health
        assert "error_handler_stats" in health
        assert "circuit_breaker_stats" in health
        assert "timestamp" in health

        # Should be healthy initially
        assert health["healthy"] is True
        assert len(health["unhealthy_services"]) == 0


if __name__ == "__main__":
    # Run specific test for debugging
    pytest.main([__file__, "-v"])
