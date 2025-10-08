# 🏆 Best Practices Guide - Namaskah.App

## Code Quality Standards

### Python Code Style
- **PEP 8 Compliance**: Follow Python style guide
- **Black Formatting**: Consistent code formatting
- **Type Hints**: Use type annotations for better code clarity
- **Docstrings**: Document all functions, classes, and modules
- **Import Organization**: Use isort for consistent imports

### Code Organization
```python
# Good: Clear function with type hints and docstring
async def create_verification_session(
    service_name: str, 
    capability: str, 
    user_id: str
) -> VerificationSession:
    """
    Create a new SMS verification session.
    
    Args:
        service_name: Name of the service (e.g., 'whatsapp')
        capability: Type of verification ('sms' or 'voice')
        user_id: ID of the requesting user
        
    Returns:
        VerificationSession: Created verification session
        
    Raises:
        ValidationError: If service_name is invalid
        ServiceUnavailableError: If service is temporarily unavailable
    """
    # Implementation here
```

### Error Handling
```python
# Good: Specific exception handling
try:
    result = await external_service.call()
except ServiceTimeoutError:
    logger.warning("Service timeout, retrying...")
    raise RetryableError("Service temporarily unavailable")
except AuthenticationError:
    logger.error("Authentication failed")
    raise ServiceError("Invalid credentials")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise ServiceError("Internal service error")
```

## Security Best Practices

### Authentication & Authorization
```python
# Good: Proper JWT validation
@require_auth
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    """Protected endpoint requiring authentication."""
    return {"user_id": current_user.id}

# Good: Role-based access control
@require_role("admin")
async def admin_endpoint(current_user: User = Depends(get_current_admin)):
    """Admin-only endpoint."""
    return {"admin_data": "sensitive"}
```

### Input Validation
```python
# Good: Pydantic models for validation
class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, regex=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]")
    full_name: str = Field(..., min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, regex=r"^\+[1-9]\d{1,14}$")

# Good: Input sanitization
def sanitize_html_content(content: str) -> str:
    """Sanitize HTML content to prevent XSS."""
    return bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
```

### Database Security
```python
# Good: Parameterized queries (SQLAlchemy ORM handles this)
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

# Good: Password hashing
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
```

## Performance Best Practices

### Database Optimization
```python
# Good: Efficient queries with proper indexing
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)  # Indexed for fast lookups
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # For time-based queries

# Good: Pagination for large datasets
async def get_users_paginated(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()
```

### Async Programming
```python
# Good: Proper async/await usage
async def process_multiple_requests(requests: List[Request]) -> List[Response]:
    """Process multiple requests concurrently."""
    tasks = [process_single_request(req) for req in requests]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Good: Connection pooling
async def get_database_connection():
    """Get database connection from pool."""
    async with database_pool.acquire() as connection:
        yield connection
```

### Caching Strategy
```python
# Good: Redis caching for expensive operations
@cache_result(ttl=300)  # Cache for 5 minutes
async def get_user_verification_status(user_id: str) -> dict:
    """Get user verification status with caching."""
    # Expensive database query here
    return verification_status

# Good: In-memory caching for static data
@lru_cache(maxsize=1000)
def get_country_code_info(country_code: str) -> dict:
    """Get country information (cached)."""
    return COUNTRY_DATA.get(country_code, {})
```

## API Design Best Practices

### RESTful Design
```python
# Good: RESTful endpoint design
@router.post("/api/users", status_code=201, response_model=UserResponse)
async def create_user(user_data: UserCreate) -> UserResponse:
    """Create a new user."""
    
@router.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str) -> UserResponse:
    """Get user by ID."""
    
@router.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate) -> UserResponse:
    """Update user information."""
    
@router.delete("/api/users/{user_id}", status_code=204)
async def delete_user(user_id: str) -> None:
    """Delete user."""
```

### Response Models
```python
# Good: Consistent response models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime
    is_verified: bool
    
    class Config:
        from_attributes = True  # For SQLAlchemy models
```

### Error Handling
```python
# Good: Consistent error responses
class APIError(HTTPException):
    def __init__(self, status_code: int, message: str, details: Optional[dict] = None):
        self.status_code = status_code
        self.detail = {
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }

# Good: Custom exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "message": "Validation failed",
            "errors": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Testing Best Practices

### Test Structure
```python
# Good: Clear test structure
class TestUserAuthentication:
    """Test user authentication functionality."""
    
    def test_successful_registration(self, client, test_user_data):
        """Test successful user registration."""
        # Arrange
        user_data = test_user_data
        
        # Act
        response = client.post("/api/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 201
        assert "access_token" in response.json()
        assert response.json()["user"]["email"] == user_data["email"]
    
    def test_duplicate_email_registration(self, client, test_user_data):
        """Test registration with duplicate email fails."""
        # Arrange
        client.post("/api/auth/register", json=test_user_data)
        
        # Act
        response = client.post("/api/auth/register", json=test_user_data)
        
        # Assert
        assert response.status_code == 400
        assert "already exists" in response.json()["message"].lower()
```

### Mocking External Services
```python
# Good: Proper mocking
@pytest.fixture
def mock_twilio_client():
    with patch('services.sms_service.twilio_client') as mock:
        mock.messages.create.return_value = Mock(
            sid="SM123456789",
            status="sent"
        )
        yield mock

def test_send_sms_success(mock_twilio_client):
    """Test successful SMS sending."""
    result = send_sms("+1234567890", "Test message")
    
    assert result.success is True
    mock_twilio_client.messages.create.assert_called_once()
```

## Deployment Best Practices

### Environment Configuration
```python
# Good: Environment-based configuration
class Settings(BaseSettings):
    app_name: str = "Namaskah.App"
    debug: bool = False
    database_url: str
    jwt_secret_key: str
    redis_url: Optional[str] = None
    
    # External service configurations
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    textverified_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Health Checks
```python
# Good: Comprehensive health checks
@router.get("/health")
async def health_check():
    """Comprehensive health check."""
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "external_services": await check_external_services()
    }
    
    is_healthy = all(checks.values())
    status_code = 200 if is_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### Logging
```python
# Good: Structured logging
import structlog

logger = structlog.get_logger()

async def process_verification(verification_id: str):
    """Process verification with proper logging."""
    logger.info(
        "Processing verification",
        verification_id=verification_id,
        user_id=current_user.id
    )
    
    try:
        result = await verification_service.process(verification_id)
        logger.info(
            "Verification processed successfully",
            verification_id=verification_id,
            result_status=result.status
        )
        return result
    except Exception as e:
        logger.error(
            "Verification processing failed",
            verification_id=verification_id,
            error=str(e),
            exc_info=True
        )
        raise
```

## Monitoring and Observability

### Metrics Collection
```python
# Good: Application metrics
from prometheus_client import Counter, Histogram, Gauge

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_users = Gauge('active_users_total', 'Number of active users')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)
    
    return response
```

### Error Tracking
```python
# Good: Sentry integration
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=settings.environment
)

# Good: Custom error context
def add_error_context(user_id: str, operation: str):
    """Add context to error tracking."""
    sentry_sdk.set_context("user", {"id": user_id})
    sentry_sdk.set_context("operation", {"name": operation})
```

## Documentation Best Practices

### API Documentation
```python
# Good: Comprehensive API documentation
@router.post(
    "/api/verification/create",
    response_model=VerificationResponse,
    status_code=201,
    summary="Create SMS verification session",
    description="Creates a new SMS verification session for the specified service",
    responses={
        201: {"description": "Verification session created successfully"},
        400: {"description": "Invalid service name or capability"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def create_verification(
    verification_data: VerificationCreate,
    current_user: User = Depends(get_current_user)
) -> VerificationResponse:
    """
    Create a new SMS verification session.
    
    This endpoint creates a verification session for the specified service
    and returns the session details including the verification ID.
    """
```

### Code Documentation
```python
# Good: Comprehensive docstrings
class VerificationService:
    """
    Service for managing SMS verification sessions.
    
    This service handles the creation, management, and cleanup of SMS
    verification sessions across multiple providers.
    
    Attributes:
        textverified_client: Client for TextVerified API
        twilio_client: Client for Twilio API
        redis_client: Redis client for session storage
    """
    
    async def create_session(
        self, 
        service_name: str, 
        capability: str,
        user_id: str
    ) -> VerificationSession:
        """
        Create a new verification session.
        
        Args:
            service_name: Name of the service to verify (e.g., 'whatsapp')
            capability: Type of verification ('sms' or 'voice')
            user_id: ID of the user requesting verification
            
        Returns:
            VerificationSession: The created verification session
            
        Raises:
            InvalidServiceError: If service_name is not supported
            QuotaExceededError: If user has exceeded verification quota
            ServiceUnavailableError: If verification service is unavailable
            
        Example:
            >>> session = await service.create_session('whatsapp', 'sms', 'user123')
            >>> print(session.verification_id)
            'ver_abc123'
        """
```

## Code Review Checklist

### Before Submitting PR
- [ ] Code follows style guidelines (Black, isort, flake8)
- [ ] All tests pass
- [ ] Code coverage meets requirements (80%+)
- [ ] Security considerations addressed
- [ ] Performance impact evaluated
- [ ] Documentation updated
- [ ] Error handling implemented
- [ ] Logging added for important operations

### Review Criteria
- [ ] Code is readable and maintainable
- [ ] Business logic is correct
- [ ] Edge cases are handled
- [ ] Security vulnerabilities addressed
- [ ] Performance optimizations applied
- [ ] Tests are comprehensive
- [ ] Documentation is accurate
- [ ] Breaking changes are documented