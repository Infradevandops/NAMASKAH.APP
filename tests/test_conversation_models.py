#!/usr/bin/env python3
"""
Unit tests for conversation and message models
"""
import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.conversation_models import (
    Conversation,
    Message,
    ConversationStatus,
    MessageType,
    conversation_participants,
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


class TestConversationModel:
    """Test cases for Conversation model"""

    def test_conversation_creation(self, db_session):
        """Test creating a conversation with valid data"""
        user = User(
            email="convuser@example.com",
            username="convuser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        conv = Conversation(
            title="Test Conversation",
            is_group=True,
            created_by=user.id,
            status=ConversationStatus.ACTIVE
        )
        db_session.add(conv)
        db_session.commit()

        assert conv.id is not None
        assert conv.title == "Test Conversation"
        assert conv.is_group is True
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.created_by == user.id
        assert isinstance(conv.created_at, datetime)

    def test_conversation_repr(self, db_session):
        """Test string representation of conversation"""
        conv = Conversation(
            title="Repr Test",
            is_group=False,
            created_by=str(uuid.uuid4()),
            status=ConversationStatus.ARCHIVED
        )
        expected = f"<Conversation(id='{conv.id}', title='{conv.title}', status={conv.status.value}, group={conv.is_group})>"
        assert repr(conv) == expected


class TestMessageModel:
    """Test cases for Message model"""

    def test_message_creation(self, db_session):
        """Test creating a message with valid data"""
        user = User(
            email="msguser@example.com",
            username="msguser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        conv = Conversation(
            title="Message Conv",
            is_group=False,
            created_by=user.id,
            status=ConversationStatus.ACTIVE
        )
        db_session.add(conv)
        db_session.commit()

        msg = Message(
            conversation_id=conv.id,
            sender_id=user.id,
            content="Hello, world!",
            message_type=MessageType.CHAT,
            is_delivered=True,
            is_read=False
        )
        db_session.add(msg)
        db_session.commit()

        assert msg.id is not None
        assert msg.conversation_id == conv.id
        assert msg.sender_id == user.id
        assert msg.content == "Hello, world!"
        assert msg.is_delivered is True
        assert msg.is_read is False

    def test_message_repr(self, db_session):
        """Test string representation of message"""
        msg = Message(
            conversation_id=str(uuid.uuid4()),
            content="Test message",
            message_type=MessageType.SYSTEM
        )
        expected = f"<Message(id='{msg.id}', conversation_id='{msg.conversation_id}', type={msg.message_type.value})>"
        assert repr(msg) == expected


class TestConversationParticipants:
    """Test conversation participants association table"""

    def test_participant_association(self, db_session):
        """Test adding and querying conversation participants"""
        user = User(
            email="partuser@example.com",
            username="partuser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        conv = Conversation(
            title="Participant Conv",
            is_group=True,
            created_by=user.id,
            status=ConversationStatus.ACTIVE
        )
        db_session.add(conv)
        db_session.commit()

        # Add participant
        conv.participants.append(user)
        db_session.commit()

        # Query participants
        loaded_conv = db_session.query(Conversation).filter_by(id=conv.id).first()
        assert user in loaded_conv.participants

        # Check association table columns
        conn = db_session.connection()
        result = conn.execute(
            f"SELECT * FROM conversation_participants WHERE conversation_id='{conv.id}' AND user_id='{user.id}'"
        )
        row = result.fetchone()
        assert row is not None
        assert row['is_admin'] is False
        assert row['notifications_enabled'] is True


if __name__ == "__main__":
    pytest.main([__file__])
