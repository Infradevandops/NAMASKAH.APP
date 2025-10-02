#!/usr/bin/env python3
"""
Comprehensive Error Handler for CumApp Communication Platform
Combines retry logic, circuit breakers, and error reporting for robust error handling
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

from core.circuit_breaker import (CircuitBreaker, CircuitBreakerConfig,
                                  ServiceCircuitConfigs, circuit_manager)
from core.exceptions import (ServiceError, DatabaseError,
                             ExternalServiceError, TextVerifiedError,
                             TwilioError, map_http_error,
                             map_twilio_error)
from core.retry_handler import RetryConfig, RetryHandler, ServiceRetryConfigs

logger = logging.getLogger(__name__)


@dataclass
class ErrorHandlerConfig:
    """Configuration for comprehensive error handling"""

    service_name: str
    enable_retry: bool = True
    enable_circuit_breaker: bool = True
    enable_error_reporting: bool = True
    retry_config: Optional[RetryConfig] = None
    circuit_config: Optional[CircuitBreakerConfig] = None
    error_mapping_func: Optional[Callable] = None


class ErrorReporter:
    """Handles error reporting and alerting"""

    def __init__(self):
        self.error_counts = {}
        self.recent_errors = []
        self.max_recent_errors = 100

    async def report_error(
        self,
        error: Exception,
        service_name: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Report an error for monitoring and alerting

        Args:
            error: Exception that occurred
            service_name: Name of the service
            operation: Operation that failed
            context: Additional context information
        """
        error_key = f"{service_name}.{operation}.{type(error).__name__}"

        # Update error counts
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0
        self.error_counts[error_key] += 1

        # Add to recent errors
        error_record = {
            "timestamp": datetime.utcnow(),
            "service": service_name,
            "operation": operation,
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context or {},
        }

        self.recent_errors.append(error_record)

        # Keep only recent errors
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors = self.recent_errors[-self.max_recent_errors :]

        # Log error with appropriate level
        if isinstance(error, ServiceError):
            if error.severity.value in ["high", "critical"]:
                logger.error(
                    f"Service error in {service_name}.{operation}: {error}",
                    exc_info=True,
                )
            else:
                logger.warning(f"Service error in {service_name}.{operation}: {error}")
        else:
            logger.error(
                f"Unexpected error in {service_name}.{operation}: {error}",
                exc_info=True,
            )

        # TODO: Add integration with monitoring systems (Sentry, DataDog, etc.)
        # await self._send_to_monitoring_system(error_record)

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "error_counts": dict(self.error_counts),
            "recent_errors": self.recent_errors[-10:],  # Last 10 errors
            "total_errors": sum(self.error_counts.values()),
        }


class ServiceErrorHandler:
    """Comprehensive error handler for a specific service"""

    def __init__(self, config: ErrorHandlerConfig):
        """
        Initialize service error handler

        Args:
            config: Error handler configuration
        """
        self.config = config
        self.service_name = config.service_name

        # Initialize components
        self.retry_handler = None
        self.circuit_breaker = None
        self.error_reporter = ErrorReporter()

        if config.enable_retry:
            retry_config = config.retry_config or self._get_default_retry_config()
            self.retry_handler = RetryHandler(retry_config)

        if config.enable_circuit_breaker:
            circuit_config = config.circuit_config or self._get_default_circuit_config()
            self.circuit_breaker = circuit_manager.get_breaker(
                f"{self.service_name}_circuit", circuit_config
            )

    def _get_default_retry_config(self) -> RetryConfig:
        """Get default retry configuration for the service"""
        service_configs = {
            "textverified": ServiceRetryConfigs.textverified,
            "twilio": ServiceRetryConfigs.twilio,
            "database": ServiceRetryConfigs.database,
            "ai_service": ServiceRetryConfigs.ai_service,
        }

        config_func = service_configs.get(self.service_name.lower())
        return config_func() if config_func else RetryConfig()

    def _get_default_circuit_config(self) -> CircuitBreakerConfig:
        """Get default circuit breaker configuration for the service"""
        service_configs = {
            "textverified": ServiceCircuitConfigs.textverified,
            "twilio": ServiceCircuitConfigs.twilio,
            "database": ServiceCircuitConfigs.database,
        }

        config_func = service_configs.get(self.service_name.lower())
        return config_func() if config_func else CircuitBreakerConfig()

    def _map_exception(self, error: Exception) -> Exception:
        """Map generic exceptions to service-specific exceptions"""
        if self.config.error_mapping_func:
            return self.config.error_mapping_func(error)

        # Default mapping based on service name
        if self.service_name.lower() == "textverified" and not isinstance(
            error, TextVerifiedError
        ):
            # Try to map to TextVerified exception
            if hasattr(error, "response") and hasattr(error.response, "status_code"):
                return map_http_error(
                    str(error.response.status_code), str(error)
                )

        elif self.service_name.lower() == "twilio" and not isinstance(
            error, TwilioError
        ):
            # Try to map to Twilio exception
            if hasattr(error, "code"):
                return map_twilio_error(str(error.code), str(error))

        return error

    async def execute_with_error_handling(
        self, func: Callable, operation_name: str, *args, **kwargs
    ) -> Any:
        """
        Execute function with comprehensive error handling

        Args:
            func: Function to execute
            operation_name: Name of the operation for logging
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        context = {
            "service": self.service_name,
            "operation": operation_name,
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()),
        }

        try:
            # Execute with circuit breaker if enabled
            if self.circuit_breaker:
                if self.retry_handler:
                    # Combine circuit breaker with retry
                    async def protected_func():
                        return await self.retry_handler.execute_with_retry(
                            func, *args, operation_name=operation_name, **kwargs
                        )

                    result = await self.circuit_breaker.call(protected_func)
                else:
                    # Circuit breaker only
                    result = await self.circuit_breaker.call(func, *args, **kwargs)

            elif self.retry_handler:
                # Retry only
                result = await self.retry_handler.execute_with_retry(
                    func, *args, operation_name=operation_name, **kwargs
                )

            else:
                # No protection, direct execution
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

            return result

        except Exception as e:
            # Map to service-specific exception
            mapped_error = self._map_exception(e)

            # Report error if enabled
            if self.config.enable_error_reporting:
                await self.error_reporter.report_error(
                    mapped_error, self.service_name, operation_name, context
                )

            # Re-raise the mapped exception
            raise mapped_error

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive error handling statistics"""
        stats = {
            "service_name": self.service_name,
            "error_stats": self.error_reporter.get_error_stats(),
        }

        if self.retry_handler:
            stats["retry_stats"] = self.retry_handler.get_stats()

        if self.circuit_breaker:
            stats["circuit_breaker_stats"] = self.circuit_breaker.get_stats()

        return stats


class ErrorHandlerManager:
    """Manages error handlers for different services"""

    def __init__(self):
        self.handlers: Dict[str, ServiceErrorHandler] = {}

    def get_handler(
        self, service_name: str, config: Optional[ErrorHandlerConfig] = None
    ) -> ServiceErrorHandler:
        """Get or create an error handler for a service"""
        if service_name not in self.handlers:
            if config is None:
                config = ErrorHandlerConfig(service_name=service_name)
            self.handlers[service_name] = ServiceErrorHandler(config)

        return self.handlers[service_name]

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all error handlers"""
        return {name: handler.get_stats() for name, handler in self.handlers.items()}


# Global error handler manager
error_manager = ErrorHandlerManager()


def with_error_handling(
    service_name: str,
    operation_name: Optional[str] = None,
    enable_retry: bool = True,
    enable_circuit_breaker: bool = True,
    enable_error_reporting: bool = True,
):
    """
    Decorator to add comprehensive error handling to functions

    Args:
        service_name: Name of the service
        operation_name: Name of the operation (defaults to function name)
        enable_retry: Whether to enable retry logic
        enable_circuit_breaker: Whether to enable circuit breaker
        enable_error_reporting: Whether to enable error reporting
    """

    def decorator(func):
        config = ErrorHandlerConfig(
            service_name=service_name,
            enable_retry=enable_retry,
            enable_circuit_breaker=enable_circuit_breaker,
            enable_error_reporting=enable_error_reporting,
        )
        handler = error_manager.get_handler(service_name, config)
        op_name = operation_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await handler.execute_with_error_handling(
                func, op_name, *args, **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to run in an event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(
                handler.execute_with_error_handling(func, op_name, *args, **kwargs)
            )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Convenience decorators for specific services
def textverified_error_handling(operation_name: Optional[str] = None):
    """Error handling decorator for TextVerified operations"""
    return with_error_handling("textverified", operation_name)


def twilio_error_handling(operation_name: Optional[str] = None):
    """Error handling decorator for Twilio operations"""
    return with_error_handling("twilio", operation_name)


def database_error_handling(operation_name: Optional[str] = None):
    """Error handling decorator for database operations"""
    return with_error_handling("database", operation_name)


def ai_service_error_handling(operation_name: Optional[str] = None):
    """Error handling decorator for AI service operations"""
    return with_error_handling("ai_service", operation_name)


def handle_errors(func):
    """
    General error handling decorator for WebRTC operations

    Args:
        func: Function to wrap with error handling

    Returns:
        Wrapped function with error handling
    """
    return with_error_handling("webrtc", func.__name__)(func)


# Health check function
async def get_error_handling_health() -> Dict[str, Any]:
    """Get health status of all error handling components"""
    stats = error_manager.get_all_stats()
    circuit_stats = circuit_manager.get_all_stats()
    unhealthy_services = circuit_manager.get_unhealthy_services()

    return {
        "healthy": len(unhealthy_services) == 0,
        "unhealthy_services": unhealthy_services,
        "error_handler_stats": stats,
        "circuit_breaker_stats": circuit_stats,
        "timestamp": datetime.utcnow().isoformat(),
    }
