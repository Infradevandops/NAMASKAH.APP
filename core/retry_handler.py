#!/usr/bin/env python3
"""
Retry Logic with Exponential Backoff
Handles retries for external service calls with circuit breaker patterns
"""
import asyncio
import time
import random
import logging
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass

from core.exceptions import (
    ServiceError, TextVerifiedError, TwilioError, AIServiceError,
    TextVerifiedRateLimitError, TwilioRateLimitError, ServiceTimeoutError,
    TextVerifiedServiceUnavailableError, GroqAPIError
)

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True
    retryable_exceptions: Optional[List[type]] = None

    def __post_init__(self):
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [
                TextVerifiedRateLimitError,
                TwilioRateLimitError,
                ServiceTimeoutError,
                TextVerifiedServiceUnavailableError
            ]


class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        if config is None:
            config = RetryConfig()
        
        self.config = config
        self.max_retries = config.max_retries
        self.base_delay = config.base_delay
        self.max_delay = config.max_delay
        self.strategy = config.strategy
        self.jitter = config.jitter
        self.retryable_exceptions = config.retryable_exceptions
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt"""
        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (2 ** attempt)
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * attempt
        elif self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.base_delay
        else:  # IMMEDIATE
            delay = 0
        
        # Apply maximum delay limit
        delay = min(delay, self.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.jitter and delay > 0:
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def _is_retryable(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)

    def _perform_retry(
        self,
        execute_func: Callable[[], Any],
        operation_name: str,
        is_async: bool = False
    ) -> Any:
        """Perform retry logic with the given execution function"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return execute_func()

            except Exception as e:
                last_exception = e

                if attempt == self.max_retries:
                    logger.error(f"Function {operation_name} failed after {self.max_retries} retries: {e}")
                    raise

                if not self._is_retryable(e):
                    logger.error(f"Non-retryable error in {operation_name}: {e}")
                    raise

                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {operation_name}: {e}. Retrying in {delay:.2f}s")

                # Check if exception specifies retry_after
                if hasattr(e, 'retry_after') and e.retry_after:
                    delay = max(delay, e.retry_after)

                if is_async:
                    # This would be called from async context
                    pass  # Delay handled by caller
                else:
                    time.sleep(delay)

        raise last_exception

    def retry(self, func: Callable) -> Callable:
        """Decorator for adding retry logic to functions"""
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt == self.max_retries:
                        logger.error(f"Function {func.__name__} failed after {self.max_retries} retries: {e}")
                        raise
                    
                    if not self._is_retryable(e):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                    
                    # Check if exception specifies retry_after
                    if hasattr(e, 'retry_after') and e.retry_after:
                        delay = max(delay, e.retry_after)
                    
                    time.sleep(delay)
            
            raise last_exception
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt == self.max_retries:
                        logger.error(f"Async function {func.__name__} failed after {self.max_retries} retries: {e}")
                        raise
                    
                    if not self._is_retryable(e):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                    
                    # Check if exception specifies retry_after
                    if hasattr(e, 'retry_after') and e.retry_after:
                        delay = max(delay, e.retry_after)
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    async def execute_with_retry(self, func: Callable, *args, operation_name: str = None, **kwargs) -> Any:
        """Execute function with retry logic"""
        op_name = operation_name or func.__name__

        async def execute_attempt():
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await execute_attempt()

            except Exception as e:
                last_exception = e

                if attempt == self.max_retries:
                    logger.error(f"Function {op_name} failed after {self.max_retries} retries: {e}")
                    raise

                if not self._is_retryable(e):
                    logger.error(f"Non-retryable error in {op_name}: {e}")
                    raise

                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {op_name}: {e}. Retrying in {delay:.2f}s")

                # Check if exception specifies retry_after
                if hasattr(e, 'retry_after') and e.retry_after:
                    delay = max(delay, e.retry_after)

                await asyncio.sleep(delay)

        raise last_exception
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry handler statistics"""
        return {
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "strategy": self.strategy.value,
            "jitter": self.jitter,
            "retryable_exceptions": [exc.__name__ for exc in self.retryable_exceptions]
        }


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
):
    """Decorator to add retry logic"""
    def decorator(func: Callable) -> Callable:
        config = RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            strategy=strategy
        )
        retry_handler = RetryHandler(config)
        return retry_handler.retry(func)
    return decorator


# Service-specific retry decorators
def textverified_retry_decorator(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """Retry decorator specifically for TextVerified operations"""
    config = RetryConfig(
        max_retries=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retryable_exceptions=[
            TextVerifiedRateLimitError,
            TextVerifiedServiceUnavailableError,
            ServiceTimeoutError
        ]
    )
    
    def decorator(func):
        retry_handler = RetryHandler(config)
        return retry_handler.retry(func)
    return decorator


def twilio_retry_decorator(max_attempts: int = 2, base_delay: float = 1.0, max_delay: float = 15.0):
    """Retry decorator specifically for Twilio operations"""
    config = RetryConfig(
        max_retries=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retryable_exceptions=[
            TwilioRateLimitError,
            ServiceTimeoutError
        ]
    )
    
    def decorator(func):
        retry_handler = RetryHandler(config)
        return retry_handler.retry(func)
    return decorator


class ServiceRetryConfigs:
    """Predefined retry configurations for different services"""
    
    @staticmethod
    def textverified() -> RetryConfig:
        """Retry configuration for TextVerified service"""
        return RetryConfig(
            max_retries=3,
            base_delay=2.0,
            max_delay=30.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=True,
            retryable_exceptions=[
                TextVerifiedRateLimitError,
                TextVerifiedServiceUnavailableError,
                ServiceTimeoutError
            ]
        )
    
    @staticmethod
    def twilio() -> RetryConfig:
        """Retry configuration for Twilio service"""
        return RetryConfig(
            max_retries=2,
            base_delay=1.0,
            max_delay=15.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=True,
            retryable_exceptions=[
                TwilioRateLimitError,
                ServiceTimeoutError
            ]
        )
    
    @staticmethod
    def database() -> RetryConfig:
        """Retry configuration for database operations"""
        return RetryConfig(
            max_retries=3,
            base_delay=0.5,
            max_delay=10.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=True,
            retryable_exceptions=[
                ServiceTimeoutError
            ]
        )
    
    @staticmethod
    def ai_service() -> RetryConfig:
        """Retry configuration for AI services (Groq, etc.)"""
        return RetryConfig(
            max_retries=2,
            base_delay=1.5,
            max_delay=20.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter=True,
            retryable_exceptions=[
                ServiceTimeoutError,
                GroqAPIError
            ]
        )