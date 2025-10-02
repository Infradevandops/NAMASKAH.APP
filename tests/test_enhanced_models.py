#!/usr/bin/env python3
"""
Unit tests for enhanced models
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models.enhanced_models import (
    UserNumber, EnhancedMessage, CountryRouting, RoutingDecision,
    InboxFolder, MessageFolder,
    MessageCategory, RoutingType, CountryTier
)
from models.user_models import User
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


class TestUserNumberModel:
    """Test cases for UserNumber model"""

    def test_user_number_creation(self, db_session):
        """Test creating a user number"""
        user = User(email="test@example.com", username="testuser", hashed_password="pass")
        db_session.add(user)
        db_session.commit()

        user_number = UserNumber(
            user_id=user.id,
            phone_number="+1234567890",
            country_code="US",
            country_name="United States",
            provider="twilio",
            routing_type=RoutingType.DIRECT,
            supports_sms=True,
            supports_voice=True,
            monthly_cost=2.00,
            sms_cost_outbound=0.01,
            voice_cost_per_minute=0.02,
            status="active",
            is_primary=True,
        )
        db_session.add(user_number)
        db_session.commit()

        assert user_number.id is not None
        assert user_number.user_id == user.id
        assert user_number.phone_number == "+1234567890"
        assert user_number.country_code == "US"
        assert user_number.status == "active"


class TestEnhancedMessageModel:
    """Test cases for EnhancedMessage model"""

    def test_enhanced_message_creation(self, db_session):
        """Test creating an enhanced message"""
        user = User(email="test@example.com", username="testuser", hashed_password="pass")
        db_session.add(user)
        db_session.commit()

        message = EnhancedMessage(
            user_id=user.id,
            category=MessageCategory.VERIFICATION_CODE,
            subcategory="sms",
            content="Your verification code is 123456",
            from_number="+1234567890",
            to_number="+0987654321",
            direction="inbound",
            message_type="sms",
            provider="twilio",
            routing_type=RoutingType.DIRECT,
            status="received",
            is_read=False,
            is_starred=False,
            extracted_codes=["123456"],
            auto_extracted=True,
            cost=0.01,
            currency="USD",
        )
        db_session.add(message)
        db_session.commit()

        assert message.id is not None
        assert message.user_id == user.id
        assert message.category == MessageCategory.VERIFICATION_CODE
        assert message.content == "Your verification code is 123456"
        assert message.extracted_codes == ["123456"]


class TestCountryRoutingModel:
    """Test cases for CountryRouting model"""

    def test_country_routing_creation(self, db_session):
        """Test creating country routing configuration"""
        country_routing = CountryRouting(
            country_code="US",
            country_name="United States",
            continent="North America",
            region="North America",
            tier=CountryTier.TIER_1,
            dial_code="+1",
            preferred_routing_type=RoutingType.SMART_ROUTING,
            supports_local_numbers=True,
            sms_cost_direct=0.05,
            sms_cost_local=0.02,
            voice_cost_per_minute=0.10,
            local_number_monthly_cost=2.00,
            delivery_success_rate=0.95,
            average_delivery_time=5,
            available_providers=["twilio", "textverified"],
            recommended_provider="twilio",
            is_active=True,
        )
        db_session.add(country_routing)
        db_session.commit()

        assert country_routing.id is not None
        assert country_routing.country_code == "US"
        assert country_routing.tier == CountryTier.TIER_1
        assert country_routing.delivery_success_rate == 0.95


class TestRoutingDecisionModel:
    """Test cases for RoutingDecision model"""

    def test_routing_decision_creation(self, db_session):
        """Test creating a routing decision log"""
        user = User(email="test@example.com", username="testuser", hashed_password="pass")
        db_session.add(user)
        db_session.commit()

        decision = RoutingDecision(
            user_id=user.id,
            destination_country="US",
            routing_type_chosen=RoutingType.SMART_ROUTING,
            decision_reason="Cost optimization",
            estimated_cost=0.02,
            actual_cost=0.02,
            cost_savings=0.03,
            delivery_time=3,
            delivery_success=True,
            ml_confidence_score=0.85,
        )
        db_session.add(decision)
        db_session.commit()

        assert decision.id is not None
        assert decision.user_id == user.id
        assert decision.routing_type_chosen == RoutingType.SMART_ROUTING
        assert decision.delivery_success is True


class TestInboxFolderModel:
    """Test cases for InboxFolder model"""

    def test_inbox_folder_creation(self, db_session):
        """Test creating an inbox folder"""
        user = User(email="test@example.com", username="testuser", hashed_password="pass")
        db_session.add(user)
        db_session.commit()

        folder = InboxFolder(
            user_id=user.id,
            name="Important",
            description="Important messages",
            color="#FF0000",
            icon="star",
            is_system_folder=False,
            auto_categorize=False,
            sort_order=1,
            is_visible=True,
        )
        db_session.add(folder)
        db_session.commit()

        assert folder.id is not None
        assert folder.user_id == user.id
        assert folder.name == "Important"
        assert folder.is_system_folder is False


class TestMessageFolderModel:
    """Test cases for MessageFolder model"""

    def test_message_folder_creation(self, db_session):
        """Test creating a message-folder association"""
        user = User(email="test@example.com", username="testuser", hashed_password="pass")
        db_session.add(user)
        db_session.commit()

        message = EnhancedMessage(
            user_id=user.id,
            category=MessageCategory.CONVERSATION,
            content="Test message",
            from_number="+1234567890",
            to_number="+0987654321",
            direction="inbound",
            provider="twilio",
        )
        db_session.add(message)

        folder = InboxFolder(
            user_id=user.id,
            name="Test Folder",
        )
        db_session.add(folder)
        db_session.commit()

        message_folder = MessageFolder(
            message_id=message.id,
            folder_id=folder.id,
            added_by_rule=False,
        )
        db_session.add(message_folder)
        db_session.commit()

        assert message_folder.id is not None
        assert message_folder.message_id == message.id
        assert message_folder.folder_id == folder.id


if __name__ == "__main__":
    pytest.main([__file__])
