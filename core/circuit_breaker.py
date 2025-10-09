#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation for namaskah Communication Platform
Provides fault tolerance and prevents cascading failures in external API calls
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

from core.exceptions import ServiceError, is_retryable_error

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""

    failure_threshold: int = 5  # Number of failures to open circuit
    recovery_timeout: float = 60.0  # Seconds to wait before trying half-open
    success_threshold: int = 3  # Successful calls needed to close circuit
    timeout: float = 30.0  # Request timeout in seconds
    expected_exception: type = Exception  # Exception type that counts as failure

    # Monitoring window settings
    window_size: int = 100  # Size of the sliding window
    minimum_requests: int = 10  # Minimum requests before considering failure rate


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""

    def __init__(self, service_name: str, state: CircuitState):
        self.service_name = service_name
        self.state = state
        super().__init__(
            f"Circuit breaker is {state.value} for service: {service_name}"
        )


class CircuitBreaker:
    """Circuit breaker implementation with sliding window failure detection"""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker

        Args:
            name: Name of the service/circuit
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.next_attempt_time = 0

        # Sliding window for failure rate calculation
        self.request_history: List[Dict[str, Any]] = []
        self.lock = Lock()

        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_open_count": 0,
            "circuit_half_open_count": 0,
            "fast_failures": 0,
        }

        logger.info(f"Circuit breaker '{name}' initialized with config: {config}")

    def _record_request(
        self, success: bool, duration: float, exception: Optional[Exception] = None
    ):
        """Record a request in the sliding window"""
        with self.lock:
            current_time = time.time()

            # Add new request to history
            self.request_history.append(
                {
                    "timestamp": current_time,
                    "success": success,
                    "duration": duration,
                    "exception_type": type(exception).__name__ if exception else None,
                }
            )

            # Remove old requests outside the window (last 5 minutes)
            window_start = current_time - 300  # 5 minutes
            self.request_history = [
                req for req in self.request_history if req["timestamp"] > window_start
            ]

            # Keep only the last N requests
            if len(self.request_history) > self.config.window_size:
                self.request_history = self.request_history[-self.config.window_size :]

            # Update statistics
            self.stats["total_requests"] += 1
            if success:
                self.stats["successful_requests"] += 1
            else:
                self.stats["failed_requests"] += 1

    def _get_failure_rate(self) -> float:
        """Calculate current failure rate from sliding window"""
        with self.lock:
            if len(self.request_history) < self.config.minimum_requests:
                return 0.0

            failed_requests = sum(
                1 for req in self.request_history if not req["success"]
            )
            return failed_requests / len(self.request_history)

    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on failure rate"""
        failure_rate = self._get_failure_rate()
        recent_requests = len(self.request_history)

        # Need minimum requests and high failure rate
        return (
            recent_requests >= self.config.minimum_requests
            and failure_rate >= 0.5  # 50% failure rate threshold
        ) or self.failure_count >= self.config.failure_threshold

    def _can_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return time.time() >= self.next_attempt_time

    def _record_success(self):
        """Record a successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)

    def _record_failure(self, exception: Exception):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self._should_open_circuit():
                self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            self._open_circuit()

    def _open_circuit(self):
        """Open the circuit"""
        self.state = CircuitState.OPEN
        self.next_attempt_time = time.time() + self.config.recovery_timeout
        self.success_count = 0
        self.stats["circuit_open_count"] += 1

        logger.warning(
            f"Circuit breaker '{self.name}' opened after {self.failure_count} failures. "
            f"Next attempt in {self.config.recovery_timeout}s"
        )

    def _close_circuit(self):
        """Close the circuit"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0

        logger.info(f"Circuit breaker '{self.name}' closed - service recovered")

    def _half_open_circuit(self):
        """Set circuit to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.stats["circuit_half_open_count"] += 1

        logger.info(
            f"Circuit breaker '{self.name}' half-open - testing service recovery"
        )

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Original exception: If function fails
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._can_attempt_reset():
                self._half_open_circuit()
            else:
                self.stats["fast_failures"] += 1
                raise CircuitBreakerError(self.name, self.state)

        # Execute the function
        start_time = time.time()
        try:
            # Add timeout to the call
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs), timeout=self.config.timeout
                )
            else:
                result = func(*args, **kwargs)

            # Record success
            duration = time.time() - start_time
            self._record_request(True, duration)
            self._record_success()

            return result

        except asyncio.TimeoutError as e:
            # Timeout is considered a failure
            duration = time.time() - start_time
            self._record_request(False, duration, e)
            self._record_failure(e)
            raise

        except Exception as e:
            # Check if this exception should count as a failure
            duration = time.time() - start_time

            if isinstance(e, self.config.expected_exception) or is_retryable_error(e):
                self._record_request(False, duration, e)
                self._record_failure(e)
            else:
                # Non-retryable errors don't count as circuit failures
                self._record_request(True, duration, e)

            raise

    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self.lock:
            failure_rate = self._get_failure_rate()

            return {
                **self.stats,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_rate": failure_rate,
                "requests_in_window": len(self.request_history),
                "next_attempt_time": (
                    self.next_attempt_time if self.state == CircuitState.OPEN else None
                ),
            }

    def reset(self):
        """Manually reset the circuit breaker"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.request_history.clear()

        logger.info(f"Circuit breaker '{self.name}' manually reset")

    def force_open(self):
        """Manually open the circuit breaker"""
        self._open_circuit()
        logger.warning(f"Circuit breaker '{self.name}' manually opened")


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""

    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = Lock()

    def get_breaker(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        with self.lock:
            return {
                name: breaker.get_stats() for name, breaker in self.breakers.items()
            }

    def reset_all(self):
        """Reset all circuit breakers"""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.reset()

    def get_unhealthy_services(self) -> List[str]:
        """Get list of services with open circuit breakers"""
        with self.lock:
            return [
                name
                for name, breaker in self.breakers.items()
                if breaker.get_state() == CircuitState.OPEN
            ]


# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 3,
    timeout: float = 30.0,
):
    """
    Decorator to add circuit breaker protection to functions

    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures to open circuit
        recovery_timeout: Seconds to wait before trying half-open
        success_threshold: Successful calls needed to close circuit
        timeout: Request timeout in seconds
    """

    def decorator(func):
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout=timeout,
        )
        breaker = circuit_manager.get_breaker(name, config)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to run in an event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(breaker.call(func, *args, **kwargs))

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Predefined circuit breaker configurations for services
class ServiceCircuitConfigs:
    """Predefined circuit breaker configurations for different services"""

    @staticmethod
    def textverified() -> CircuitBreakerConfig:
        """Circuit breaker configuration for TextVerified API"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=120.0,
            success_threshold=2,
            timeout=30.0,
            minimum_requests=5,
        )

    @staticmethod
    def twilio() -> CircuitBreakerConfig:
        """Circuit breaker configuration for Twilio API"""
        return CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0,
            success_threshold=3,
            timeout=20.0,
            minimum_requests=10,
        )

    @staticmethod
    def database() -> CircuitBreakerConfig:
        """Circuit breaker configuration for database operations"""
        return CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=30.0,
            success_threshold=5,
            timeout=10.0,
            minimum_requests=20,
        )


# Convenience decorators for specific services
def textverified_circuit_breaker(func):
    """Circuit breaker decorator for TextVerified API calls"""
    breaker = circuit_manager.get_breaker(
        "textverified", ServiceCircuitConfigs.textverified()
    )

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await breaker.call(func, *args, **kwargs)

    return wrapper


def twilio_circuit_breaker(func):
    """Circuit breaker decorator for Twilio API calls"""
    breaker = circuit_manager.get_breaker("twilio", ServiceCircuitConfigs.twilio())

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await breaker.call(func, *args, **kwargs)

    return wrapper


def database_circuit_breaker(func):
    """Circuit breaker decorator for database operations"""
    breaker = circuit_manager.get_breaker("database", ServiceCircuitConfigs.database())

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await breaker.call(func, *args, **kwargs)

    return wrapper
