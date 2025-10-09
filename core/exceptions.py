#!/usr/bin/env python3
"""
Service-Specific Exception Classes
Custom exceptions for TextVerified, Twilio, and other service failures
"""
from typing import Optional, Dict, Any
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceError(Exception):
    """Base class for all service-related errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        service_name: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.service_name = service_name
        self.severity = severity
        self.retry_after = retry_after
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "service_name": self.service_name,
            "severity": self.severity.value,
            "retry_after": self.retry_after,
            "context": self.context
        }


# TextVerified Exceptions
class TextVerifiedError(ServiceError):
    """Base class for TextVerified API errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, service_name="textverified", **kwargs)


class TextVerifiedAuthenticationError(TextVerifiedError):
    """TextVerified authentication/authorization errors"""
    
    def __init__(self, message: str = "TextVerified authentication failed", **kwargs):
        super().__init__(message, error_code="TV_AUTH_FAILED", severity=ErrorSeverity.HIGH, **kwargs)


class TextVerifiedRateLimitError(TextVerifiedError):
    """TextVerified rate limit exceeded"""
    
    def __init__(self, message: str = "TextVerified rate limit exceeded", retry_after: int = 60, **kwargs):
        super().__init__(
            message, 
            error_code="TV_RATE_LIMIT", 
            severity=ErrorSeverity.MEDIUM,
            retry_after=retry_after,
            **kwargs
        )


class TextVerifiedServiceUnavailableError(TextVerifiedError):
    """TextVerified service is unavailable"""
    
    def __init__(self, message: str = "TextVerified service unavailable", **kwargs):
        super().__init__(
            message, 
            error_code="TV_SERVICE_UNAVAILABLE", 
            severity=ErrorSeverity.HIGH,
            retry_after=300,  # 5 minutes
            **kwargs
        )


class TextVerifiedVerificationError(TextVerifiedError):
    """TextVerified verification-specific errors"""
    
    def __init__(self, message: str, verification_id: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if verification_id:
            context['verification_id'] = verification_id
        super().__init__(
            message, 
            error_code="TV_VERIFICATION_ERROR", 
            severity=ErrorSeverity.MEDIUM,
            context=context,
            **kwargs
        )


class TextVerifiedInsufficientBalanceError(TextVerifiedError):
    """TextVerified insufficient balance"""
    
    def __init__(self, message: str = "Insufficient TextVerified balance", **kwargs):
        super().__init__(
            message, 
            error_code="TV_INSUFFICIENT_BALANCE", 
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


# Twilio Exceptions
class TwilioError(ServiceError):
    """Base class for Twilio API errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, service_name="twilio", **kwargs)


class TwilioAuthenticationError(TwilioError):
    """Twilio authentication/authorization errors"""
    
    def __init__(self, message: str = "Twilio authentication failed", **kwargs):
        super().__init__(message, error_code="TW_AUTH_FAILED", severity=ErrorSeverity.HIGH, **kwargs)


class TwilioRateLimitError(TwilioError):
    """Twilio rate limit exceeded"""
    
    def __init__(self, message: str = "Twilio rate limit exceeded", retry_after: int = 60, **kwargs):
        super().__init__(
            message, 
            error_code="TW_RATE_LIMIT", 
            severity=ErrorSeverity.MEDIUM,
            retry_after=retry_after,
            **kwargs
        )


class TwilioInsufficientBalanceError(TwilioError):
    """Twilio insufficient balance"""
    
    def __init__(self, message: str = "Insufficient Twilio balance", **kwargs):
        super().__init__(
            message, 
            error_code="TW_INSUFFICIENT_BALANCE", 
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class TwilioNumberUnavailableError(TwilioError):
    """Twilio phone number unavailable"""
    
    def __init__(self, message: str, phone_number: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if phone_number:
            context['phone_number'] = phone_number
        super().__init__(
            message, 
            error_code="TW_NUMBER_UNAVAILABLE", 
            severity=ErrorSeverity.MEDIUM,
            context=context,
            **kwargs
        )


class TwilioMessageDeliveryError(TwilioError):
    """Twilio message delivery failure"""
    
    def __init__(self, message: str, message_sid: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if message_sid:
            context['message_sid'] = message_sid
        super().__init__(
            message, 
            error_code="TW_MESSAGE_DELIVERY_FAILED", 
            severity=ErrorSeverity.MEDIUM,
            context=context,
            **kwargs
        )


# AI Service Exceptions
class AIServiceError(ServiceError):
    """Base class for AI service errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, service_name="ai_service", **kwargs)


class GroqAPIError(AIServiceError):
    """Groq API specific errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, service_name="groq", **kwargs)


class AIModelUnavailableError(AIServiceError):
    """AI model is unavailable"""
    
    def __init__(self, message: str = "AI model unavailable", model_name: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if model_name:
            context['model_name'] = model_name
        super().__init__(
            message, 
            error_code="AI_MODEL_UNAVAILABLE", 
            severity=ErrorSeverity.MEDIUM,
            retry_after=120,
            context=context,
            **kwargs
        )


# Database Exceptions
class DatabaseError(ServiceError):
    """Base class for database errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, service_name="database", **kwargs)


class DatabaseConnectionError(DatabaseError):
    """Database connection failure"""
    
    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(
            message, 
            error_code="DB_CONNECTION_FAILED", 
            severity=ErrorSeverity.CRITICAL,
            retry_after=30,
            **kwargs
        )


class DatabaseTimeoutError(DatabaseError):
    """Database operation timeout"""
    
    def __init__(self, message: str = "Database operation timed out", **kwargs):
        super().__init__(
            message, 
            error_code="DB_TIMEOUT", 
            severity=ErrorSeverity.HIGH,
            retry_after=10,
            **kwargs
        )


# Routing Exceptions
class RoutingError(ServiceError):
    """Base class for routing errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, service_name="routing", **kwargs)


class NoRouteAvailableError(RoutingError):
    """No routing option available for destination"""
    
    def __init__(self, message: str, destination: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if destination:
            context['destination'] = destination
        super().__init__(
            message, 
            error_code="NO_ROUTE_AVAILABLE", 
            severity=ErrorSeverity.HIGH,
            context=context,
            **kwargs
        )


class RoutingOptimizationError(RoutingError):
    """Routing optimization failed"""
    
    def __init__(self, message: str = "Routing optimization failed", **kwargs):
        super().__init__(
            message, 
            error_code="ROUTING_OPTIMIZATION_FAILED", 
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


# Subscription and Billing Exceptions
class SubscriptionError(ServiceError):
    """Base class for subscription errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, service_name="subscription", **kwargs)


class InsufficientCreditsError(SubscriptionError):
    """User has insufficient credits"""
    
    def __init__(self, message: str = "Insufficient credits", required_credits: Optional[float] = None, **kwargs):
        context = kwargs.get('context', {})
        if required_credits:
            context['required_credits'] = required_credits
        super().__init__(
            message, 
            error_code="INSUFFICIENT_CREDITS", 
            severity=ErrorSeverity.HIGH,
            context=context,
            **kwargs
        )


class SubscriptionLimitExceededError(SubscriptionError):
    """Subscription limit exceeded"""
    
    def __init__(self, message: str, limit_type: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if limit_type:
            context['limit_type'] = limit_type
        super().__init__(
            message, 
            error_code="SUBSCRIPTION_LIMIT_EXCEEDED", 
            severity=ErrorSeverity.HIGH,
            context=context,
            **kwargs
        )


# Validation Exceptions
class ValidationError(ServiceError):
    """Base class for validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if field:
            context['field'] = field
        super().__init__(
            message, 
            error_code="VALIDATION_ERROR", 
            severity=ErrorSeverity.LOW,
            context=context,
            **kwargs
        )


class PhoneNumberValidationError(ValidationError):
    """Phone number validation error"""
    
    def __init__(self, message: str, phone_number: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if phone_number:
            context['phone_number'] = phone_number
        super().__init__(
            message, 
            error_code="PHONE_NUMBER_INVALID", 
            field="phone_number",
            context=context,
            **kwargs
        )


# Configuration Exceptions
class ConfigurationError(ServiceError):
    """Configuration-related errors"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        context = kwargs.get('context', {})
        if config_key:
            context['config_key'] = config_key
        super().__init__(
            message, 
            error_code="CONFIGURATION_ERROR", 
            severity=ErrorSeverity.HIGH,
            context=context,
            **kwargs
        )


# External Service Exceptions
class ExternalServiceError(ServiceError):
    """Generic external service error"""
    
    def __init__(self, message: str, service_name: str, **kwargs):
        super().__init__(message, service_name=service_name, **kwargs)


class ServiceTimeoutError(ExternalServiceError):
    """External service timeout"""
    
    def __init__(self, message: str, service_name: str, timeout_seconds: Optional[int] = None, **kwargs):
        context = kwargs.get('context', {})
        if timeout_seconds:
            context['timeout_seconds'] = timeout_seconds
        super().__init__(
            message, 
            service_name=service_name,
            error_code="SERVICE_TIMEOUT", 
            severity=ErrorSeverity.MEDIUM,
            retry_after=60,
            context=context,
            **kwargs
        )


# Error mapping for common HTTP status codes
HTTP_ERROR_MAPPING = {
    400: ValidationError,
    401: TextVerifiedAuthenticationError,  # Default to TextVerified, can be overridden
    403: TextVerifiedAuthenticationError,
    404: ValidationError,
    429: TextVerifiedRateLimitError,
    500: ExternalServiceError,
    502: ServiceTimeoutError,
    503: TextVerifiedServiceUnavailableError,
    504: ServiceTimeoutError
}


def map_http_error(status_code: int, message: str, service_name: str = "unknown") -> ServiceError:
    """Map HTTP status code to appropriate exception"""
    error_class = HTTP_ERROR_MAPPING.get(status_code, ExternalServiceError)
    
    if error_class in [ExternalServiceError, ServiceTimeoutError]:
        return error_class(message, service_name=service_name)
    else:
        return error_class(message)


def map_twilio_error(twilio_exception) -> TwilioError:
    """Map Twilio exception to appropriate namaskah exception"""
    try:
        # Handle Twilio REST exceptions
        if hasattr(twilio_exception, 'status'):
            status_code = twilio_exception.status
            message = str(twilio_exception)
            
            if status_code == 401:
                return TwilioAuthenticationError(message)
            elif status_code == 429:
                return TwilioRateLimitError(message)
            elif status_code == 400 and 'insufficient' in message.lower():
                return TwilioInsufficientBalanceError(message)
            elif status_code in [500, 502, 503, 504]:
                return TwilioError(message, error_code="TW_SERVICE_ERROR", severity=ErrorSeverity.HIGH)
            else:
                return TwilioError(message, error_code=f"TW_HTTP_{status_code}")
        
        # Handle generic Twilio errors
        message = str(twilio_exception)
        if 'auth' in message.lower() or 'credential' in message.lower():
            return TwilioAuthenticationError(message)
        elif 'rate' in message.lower() or 'limit' in message.lower():
            return TwilioRateLimitError(message)
        elif 'balance' in message.lower() or 'insufficient' in message.lower():
            return TwilioInsufficientBalanceError(message)
        else:
            return TwilioError(message, error_code="TW_GENERIC_ERROR")
            
    except Exception:
        # Fallback for any mapping errors
        return TwilioError(f"Twilio error: {str(twilio_exception)}", error_code="TW_MAPPING_ERROR")


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable based on its type and properties.
    
    Args:
        error: The exception to check
        
    Returns:
        bool: True if the error is retryable, False otherwise
    """
    # Network and timeout errors are generally retryable
    retryable_types = (
        ServiceTimeoutError,
        DatabaseConnectionError,
        DatabaseTimeoutError,
        TextVerifiedServiceUnavailableError,
        TextVerifiedRateLimitError,
        TwilioRateLimitError,
        AIModelUnavailableError,
    )
    
    if isinstance(error, retryable_types):
        return True
    
    # Check if it's a ServiceError with specific characteristics
    if isinstance(error, ServiceError):
        # Don't retry authentication errors or validation errors
        non_retryable_types = (
            TextVerifiedAuthenticationError,
            TwilioAuthenticationError,
            ValidationError,
            PhoneNumberValidationError,
            InsufficientCreditsError,
            SubscriptionLimitExceededError,
            TextVerifiedInsufficientBalanceError,
            TwilioInsufficientBalanceError,
        )
        
        if isinstance(error, non_retryable_types):
            return False
            
        # Check severity - don't retry critical errors
        if error.severity == ErrorSeverity.CRITICAL:
            return False
            
        # If it has a retry_after value, it's retryable
        if error.retry_after is not None:
            return True
    
    # For generic exceptions, check common patterns
    error_message = str(error).lower()
    retryable_patterns = [
        'timeout',
        'connection',
        'network',
        'temporary',
        'unavailable',
        'rate limit',
        'too many requests',
        'service unavailable',
        'internal server error',
        'bad gateway',
        'gateway timeout'
    ]
    
    return any(pattern in error_message for pattern in retryable_patterns)


# Alias for backward compatibility
BaseServiceException = ServiceError