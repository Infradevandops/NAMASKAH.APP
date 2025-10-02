#!/usr/bin/env python3
"""
Unit tests for communication models
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models.communication_models import (
    CommunicationSession, CommunicationMessage, VoiceCall,
    ConferenceCall, CommunicationAnalytics,
    MessageDirection, MessageStatus, CallStatus,
    CommunicationType, RoutingStrategy
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


class TestCommunicationSessionModel:
    """Test cases for CommunicationSession model"""

    def test_communication_session_creation(self, db_session):
        """Test creating a communication session"""
        user = User(email="test@example.com", username="testuser", hashed_password="pass")
        db_session.add(user)
        db_session.commit()

        session = CommunicationSession(
            user_id=user.id,
            session_type=CommunicationType.SMS,
            external_number="+1234567890",
            from_number="+0987654321",
            title="Test Session",
            description="A test communication session",
            is_active=True,
            is_archived=False,
        )
        db_session.add(session)
        db_session.commit()

        assert session.id is not None
        assert session.user_id == user.id
        assert session.session_type == CommunicationType.SMS
        assert session.external_number == "+1234567890"
        assert session.is_active is True


class TestCommunicationMessageModel:
    """Test cases for CommunicationMessage model"""

    def test_communication_message_creation(self, db_session):
        """Test creating a communication message"""
        user = User(email="test@example.com", username="testuser", hashed_password="pass")
        db_session.add(user)
        db_session.commit()

        session = CommunicationSession(
            user_id=user.id,
            session_type=CommunicationType.SMS,
            external_number="+1234567890",
            from_number="+0987654321",
        )
        db_session.add(session)
        db_session.commit()

        message = CommunicationMessage(
            session_id=session.id,
            user_id=user.id,
            direction=MessageDirection.OUTBOUND,
            message_type=CommunicationType.SMS,
            content="Hello, world!",
            from_number="+0987654321",
            to_number="+1234567890",
            provider="twilio",
            status=MessageStatus.QUEUED,
            routing_strategy=RoutingStrategy.DIRECT,
            cost=0.01,
            currency="USD",
            media_count=0,
            ai_suggested=False,
        )
        db_session.add(message)
        db_session.commit()

        assert message.id is not None
        assert message.session_id == session.id
        assert message.content == "Hello, world!"
        assert message.status == MessageStatus.QUEUED


class TestVoiceCallModel:
    """Test cases for VoiceCall model"""

    def test_voice_call_creation(self, db_session):
        """Test creating a voice call"""
        user = User(email="test@example.com", username="testuser", hashed_password="pass")
        db_session.add(user)
        db_session.commit()

        call = VoiceCall(
            user_id=user.id,
            direction=MessageDirection.OUTBOUND,
            from_number="+0987654321",
            to_number="+1234567890",
            provider="twilio",
            status=CallStatus.QUEUED,
            duration=0,
            routing_strategy=RoutingStrategy.DIRECT,
            is_recorded=False,
            is_conference_call=False,
            cost=0.02,
            currency="USD",
        )
        db_session.add(call)
        db_session.commit()

        assert call.id is not None
        assert call.user_id == user.id
        assert call.status == CallStatus.QUEUED
        assert call.duration == 0


class TestConferenceCallModel:
    """Test cases for ConferenceCall model"""

    def test_conference_call_creation(self, db_session):
        """Test creating a conference call"""
        user = User(email="test@example.com", username="testuser", hashed_password="pass")
        db_session.add(user)
        db_session.commit()

        conference = ConferenceCall(
            user_id=user.id,
            conference_name="Test Conference",
            friendly_name="Friendly Test Conference",
            provider="twilio",
            max_participants=10,
            is_recorded=False,
            status="created",
            participant_count=0,
        )
        db_session.add(conference)
        db_session.commit()

        assert conference.id is not None
        assert conference.user_id == user.id
        assert conference.conference_name == "Test Conference"
        assert conference.status == "created"


class TestCommunicationAnalyticsModel:
    """Test cases for CommunicationAnalytics model"""

    def test_communication_analytics_creation(self, db_session):
        """Test creating communication analytics"""
        analytics = CommunicationAnalytics(
            date=datetime.utcnow(),
            period_type="daily",
            sms_sent=10,
            sms_received=5,
            sms_delivered=9,
            sms_failed=1,
            calls_made=3,
            calls_received=2,
            calls_completed=2,
            total_call_duration=300,
            sms_cost=0.10,
            voice_cost=0.06,
            total_cost=0.16,
        )
        db_session.add(analytics)
        db_session.commit()

        assert analytics.id is not None
        assert analytics.sms_sent == 10
        assert analytics.calls_made == 3
        assert analytics.total_cost == 0.16


if __name__ == "__main__":
    pytest.main([__file__])
