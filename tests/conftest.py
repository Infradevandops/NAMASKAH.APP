#!/usr/bin/env python3
"""
Pytest configuration and fixtures for the Namaskah.App test suite.
"""
import asyncio
import os
import tempfile
import uuid
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set test environment before importing app modules
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-not-secure-32-chars-minimum"
os.environ["USE_MOCK_TWILIO"] = "true"
os.environ["USE_MOCK_TEXTVERIFIED"] = "true"
os.environ["DEBUG"] = "false"
os.environ["LOG_LEVEL"] = "ERROR"  # Reduce noise in tests
os.environ["RATE_LIMIT_ENABLED"] = "false"  # Disable rate limiting in tests

from main import app
from core.database import Base, get_database_url, get_db
from models.user_models import User
from models.verification_models import VerificationSession
from models.conversation_models import Conversation, Message
from auth.security import get_password_hash, create_access_token


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    test_db_url = f"sqlite:///{db_path}"
    
    # Create engine and tables
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    # Override the dependency
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield engine
    
    # Cleanup
    app.dependency_overrides.clear()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(test_db) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "phone_number": "+1234567890"
    }


@pytest.fixture
def admin_user_data():
    """Sample admin user data for testing."""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "Admin User",
        "phone_number": "+1234567891",
        "is_admin": True
    }


@pytest.fixture
def test_user_token(test_user_data):
    """Create a JWT token for testing authenticated endpoints."""
    return create_access_token(data={"sub": test_user_data["email"]})


@pytest.fixture
def admin_user_token(admin_user_data):
    """Create an admin JWT token for testing admin endpoints."""
    return create_access_token(data={"sub": admin_user_data["email"], "is_admin": True})


@pytest.fixture
def auth_headers(test_user_token):
    """Create authorization headers for testing."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_headers(admin_user_token):
    """Create admin authorization headers for testing."""
    return {"Authorization": f"Bearer {admin_user_token}"}


@pytest.fixture
def mock_verification_data():
    """Sample verification data for testing."""
    return {
        "service_name": "whatsapp",
        "capability": "sms",
        "country_code": "US"
    }


@pytest.fixture
def mock_conversation_data():
    """Sample conversation data for testing."""
    return {
        "title": "Test Conversation",
        "participants": ["test@example.com", "user2@example.com"]
    }


@pytest.fixture
def mock_message_data():
    """Sample message data for testing."""
    return {
        "content": "Hello, this is a test message",
        "message_type": "text"
    }


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client for testing."""
    mock_client = Mock()
    mock_client.messages.create.return_value = Mock(
        sid="SM123456789",
        status="sent",
        error_code=None
    )
    mock_client.calls.create.return_value = Mock(
        sid="CA123456789",
        status="initiated"
    )
    return mock_client


@pytest.fixture
def mock_textverified_client():
    """Mock TextVerified client for testing."""
    mock_client = AsyncMock()
    mock_client.create_verification.return_value = {
        "verification_id": "test_verification_123",
        "phone_number": "+1234567890",
        "status": "active"
    }
    mock_client.get_messages.return_value = [
        {"message": "Your code is 123456", "timestamp": "2024-01-01T00:00:00Z"}
    ]
    return mock_client


@pytest.fixture
def mock_groq_client():
    """Mock Groq AI client for testing."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="This is a test AI response"))]
    )
    return mock_client


@pytest.fixture
def sample_users(test_db):
    """Create sample users in the test database."""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=test_db)
    db = SessionLocal()
    
    users = []
    for i in range(3):
        user = User(
            id=str(uuid.uuid4()),
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            hashed_password=get_password_hash("password123"),
            phone_number=f"+123456789{i}",
            is_verified=True
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    db.close()
    return users


@pytest.fixture
def performance_test_data():
    """Data for performance testing."""
    return {
        "concurrent_users": 10,
        "requests_per_user": 5,
        "test_duration": 30  # seconds
    }


# Markers for test categorization
pytestmark = [
    pytest.mark.asyncio,
]