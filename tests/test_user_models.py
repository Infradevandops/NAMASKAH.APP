#!/usr/bin/env python3
"""
Unit tests for user models
"""
import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user_models import User, Session, APIKey, UserRole, SubscriptionPlan, UserCreate, UserResponse, APIKeyCreate, APIKeyResponse
from core.database import Base


@pytest.fixture(scope="module")
def test_engine():
    """Create in-memory SQLite engine for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a new database session for each test"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


class TestUserModel:
    """Test cases for User model"""

    def test_user_creation(self, db_session):
        """Test creating a user with valid data"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            full_name="Test User"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.role == UserRole.USER.value
        assert user.subscription_plan == SubscriptionPlan.FREE.value
        assert isinstance(user.created_at, datetime)

    def test_user_defaults(self, db_session):
        """Test default values for user"""
        user = User(
            email="minimal@example.com",
            username="minimal",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        assert user.full_name is None
        assert user.is_active is True
        assert user.is_verified is False
        assert user.monthly_sms_limit == 100
        assert user.monthly_sms_used == 0

    def test_user_repr(self, db_session):
        """Test string representation of user"""
        user = User(
            email="repr@example.com",
            username="repruser",
            hashed_password="pass"
        )
        expected = f"<User(id='{user.id}', username='repruser', email='repr@example.com', active=True)>"
        assert repr(user) == expected

    def test_user_unique_constraints(self, db_session):
        """Test unique constraints on email and username"""
        user1 = User(
            email="unique@example.com",
            username="uniqueuser",
            hashed_password="pass"
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create duplicate email
        user2 = User(
            email="unique@example.com",  # Same email
            username="different",
            hashed_password="pass"
        )
        db_session.add(user2)
        with pytest.raises(Exception):  # Unique constraint violation
            db_session.commit()

    @pytest.mark.parametrize("monthly_sms_used", [-1, -10])
    def test_user_sms_used_constraint(self, db_session, monthly_sms_used):
        """Test that monthly_sms_used cannot be negative"""
        user = User(
            email="constraint@example.com",
            username="constraint",
            hashed_password="pass",
            monthly_sms_used=monthly_sms_used
        )
        db_session.add(user)

        with pytest.raises(Exception):  # Check constraint violation
            db_session.commit()

    def test_user_valid_sms_used(self, db_session):
        """Test that valid monthly_sms_used values are accepted"""
        user = User(
            email="valid@example.com",
            username="valid",
            hashed_password="pass",
            monthly_sms_used=50
        )
        db_session.add(user)
        db_session.commit()

        assert user.monthly_sms_used == 50


class TestSessionModel:
    """Test cases for Session model"""

    def test_session_creation(self, db_session):
        """Test creating a session with valid data"""
        # First create a user
        user = User(
            email="session@example.com",
            username="sessionuser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        expires_at = datetime.utcnow() + timedelta(hours=24)
        session = Session(
            user_id=user.id,
            refresh_token="refresh_token_123",
            expires_at=expires_at,
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        db_session.add(session)
        db_session.commit()

        assert session.id is not None
        assert session.user_id == user.id
        assert session.refresh_token == "refresh_token_123"
        assert session.is_active is True

    def test_session_relationship(self, db_session):
        """Test session-user relationship"""
        user = User(
            email="rel@example.com",
            username="reluser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        session = Session(
            user_id=user.id,
            refresh_token="token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(session)
        db_session.commit()

        # Test relationship loading
        loaded_session = db_session.query(Session).filter_by(id=session.id).first()
        assert loaded_session.user == user
        assert loaded_session.user.username == "reluser"

    def test_session_repr(self, db_session):
        """Test string representation of session"""
        user = User(
            email="repr@example.com",
            username="repr",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        session = Session(
            user_id=user.id,
            refresh_token="token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        expected = f"<Session(id='{session.id}', user_id='{user.id}', active=True)>"
        assert repr(session) == expected


class TestAPIKeyModel:
    """Test cases for APIKey model"""

    def test_api_key_creation(self, db_session):
        """Test creating an API key with valid data"""
        # Create user first
        user = User(
            email="apikey@example.com",
            username="apikeyuser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        expires_at = datetime.utcnow() + timedelta(days=365)
        api_key = APIKey(
            user_id=user.id,
            key_hash="hash_123",
            name="Test Key",
            scopes='["read", "write"]',
            expires_at=expires_at
        )
        db_session.add(api_key)
        db_session.commit()

        assert api_key.id is not None
        assert api_key.user_id == user.id
        assert api_key.name == "Test Key"
        assert api_key.is_active is True
        assert api_key.total_requests == 0

    def test_api_key_relationship(self, db_session):
        """Test API key-user relationship"""
        user = User(
            email="apirel@example.com",
            username="apirel",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        api_key = APIKey(
            user_id=user.id,
            key_hash="hash",
            name="Test Key"
        )
        db_session.add(api_key)
        db_session.commit()

        loaded_key = db_session.query(APIKey).filter_by(id=api_key.id).first()
        assert loaded_key.user == user

    def test_api_key_repr(self, db_session):
        """Test string representation of API key"""
        user = User(
            email="apirepr@example.com",
            username="apirepr",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        api_key = APIKey(
            user_id=user.id,
            key_hash="hash",
            name="Test Key"
        )
        expected = f"<APIKey(id='{api_key.id}', name='Test Key', user_id='{user.id}', active=True)>"
        assert repr(api_key) == expected

    @pytest.mark.parametrize("total_requests", [-1, -5])
    def test_api_key_requests_constraint(self, db_session, total_requests):
        """Test that total_requests cannot be negative"""
        user = User(
            email="constraint@example.com",
            username="constraint",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        api_key = APIKey(
            user_id=user.id,
            key_hash="hash",
            name="Test",
            total_requests=total_requests
        )
        db_session.add(api_key)

        with pytest.raises(Exception):  # Check constraint violation
            db_session.commit()


class TestPydanticModels:
    """Test cases for Pydantic models"""

    def test_user_create_model(self):
        """Test UserCreate Pydantic model"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
            "full_name": "Test User"
        }
        user_create = UserCreate(**user_data)
        assert user_create.email == "test@example.com"
        assert user_create.username == "testuser"
        assert user_create.password == "password123"
        assert user_create.full_name == "Test User"

    def test_user_create_minimal(self):
        """Test UserCreate with minimal required fields"""
        user_data = {
            "email": "minimal@example.com",
            "username": "minimal",
            "password": "pass"
        }
        user_create = UserCreate(**user_data)
        assert user_create.full_name is None

    def test_user_response_model(self):
        """Test UserResponse Pydantic model"""
        user_data = {
            "id": str(uuid.uuid4()),
            "email": "response@example.com",
            "username": "response",
            "full_name": "Response User",
            "role": UserRole.USER,
            "subscription_plan": SubscriptionPlan.PREMIUM,
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow()
        }
        user_response = UserResponse(**user_data)
        assert user_response.email == "response@example.com"
        assert user_response.role == UserRole.USER

    def test_api_key_create_model(self):
        """Test APIKeyCreate Pydantic model"""
        key_data = {
            "name": "Test Key",
            "scopes": '["read"]',
            "expires_in_days": 30
        }
        api_key_create = APIKeyCreate(**key_data)
        assert api_key_create.name == "Test Key"
        assert api_key_create.expires_in_days == 30

    def test_api_key_response_model(self):
        """Test APIKeyResponse Pydantic model"""
        key_data = {
            "id": str(uuid.uuid4()),
            "name": "Response Key",
            "key_prefix": "sk_test_123",
            "scopes": '["read", "write"]',
            "is_active": True,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=365),
            "last_used": datetime.utcnow()
        }
        api_key_response = APIKeyResponse(**key_data)
        assert api_key_response.name == "Response Key"
        assert api_key_response.key_prefix == "sk_test_123"


if __name__ == "__main__":
    pytest.main([__file__])
