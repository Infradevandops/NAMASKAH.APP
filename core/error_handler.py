T^}#!/usr/bin/env python3
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

        # Send to monitoring systems
        await self._send_to_monitoring_system(error_record)

    async def _send_to_monitoring_system(self, error_record: Dict[str, Any]) -> None:
        """
        Send error record to monitoring systems (Sentry, DataDog, etc.)

        This is a placeholder for monitoring integration.
        Implement actual monitoring calls here.
        """
        # Placeholder for monitoring integration
        # Examples:
        # - Sentry: sentry_sdk.capture_exception(error_record)
        # - DataDog: datadog_api.Event.create(title="Error", text=str(error_record))
        # - Custom monitoring service

        # For now, just log that monitoring would be called
        logger.debug(f"Monitoring integration placeholder: {error_record}")

        # TODO: Implement actual monitoring system integration
        pass

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

    def _build_execution_context(
        self, operation_name: str, args: tuple, kwargs: dict
    ) -> Dict[str, Any]:
        """Build context information for error reporting"""
        return {
            "service": self.service_name,
            "operation": operation_name,
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()),
        }

    def _create_protected_function(
        self, func: Callable, operation_name: str, args: tuple, kwargs: dict
    ) -> Callable:
        """Create a protected function combining retry and circuit breaker logic"""
        if self.retry_handler:
            # Combine circuit breaker with retry
            async def protected_func():
                return await self.retry_handler.execute_with_retry(
                    func, *args, operation_name=operation_name, **kwargs
                )
            return protected_func
        else:
            # Circuit breaker only
            return func

    async def _execute_with_protection(
        self, func: Callable, operation_name: str, *args, **kwargs
    ) -> Any:
        """Execute function with appropriate protection mechanisms"""
        if self.circuit_breaker:
            protected_func = self._create_protected_function(func, operation_name, args, kwargs)
            result = await self.circuit_breaker.call(protected_func, *args, **kwargs)
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

    async def _handle_execution_error(
        self, error: Exception, operation_name: str, context: Dict[str, Any]
    ) -> None:
        """Handle execution errors by mapping and reporting"""
        # Map to service-specific exception
        mapped_error = self._map_exception(error)

        # Report error if enabled
        if self.config.enable_error_reporting:
            await self.error_reporter.report_error(
                mapped_error, self.service_name, operation_name, context
            )

        # Re-raise the mapped exception
        raise mapped_error

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
        context = self._build_execution_context(operation_name, args, kwargs)

        try:
            result = await self._execute_with_protection(func, operation_name, *args, **kwargs)
            return result
        except Exception as e:
            await self._handle_execution_error(e, operation_name, context)

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive error handling statistics"""
        stats = {
            "service_name": self.service_name,
            "error_reporter": self.error_reporter.get_error_stats(),
        }
        
        if self.retry_handler:
            stats["retry_stats"] = self.retry_handler.get_stats()
            
        if self.circuit_breaker:
            stats["circuit_breaker_stats"] = self.circuit_breaker.get_stats()
            
        return stats


# Global error handler instances
error_handlers = {}


def get_error_handler(service_name: str, config: Optional[ErrorHandlerConfig] = None) -> ServiceErrorHandler:
    """Get or create error handler for a service"""
    if service_name not in error_handlers:
        if not config:
            config = ErrorHandlerConfig(service_name=service_name)
        error_handlers[service_name] = ServiceErrorHandler(config)
    return error_handlers[service_name]


def error_handler(service_name: str, operation_name: Optional[str] = None):
    """Decorator for automatic error handling"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handler = get_error_handler(service_name)
            op_name = operation_name or func.__name__
            return await handler.execute_with_error_handling(func, op_name, *args, **kwargs)
        return wrapper
    return decorator


# Convenience decorator for common error handling patterns
def with_error_handling(service_name: str, operation_name: Optional[str] = None):
    """Alias for error_handler decorator"""
    return error_handler(service_name, operation_name)
