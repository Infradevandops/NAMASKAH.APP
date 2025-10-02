#!/usr/bin/env python3
"""
Unit tests for call models
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from models.call_models import Call, WebRTCSession
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


class TestCallModel:
    """Test cases for Call model"""

    def test_call_creation(self, db_session):
        """Test creating a call record"""
        caller = User(email="caller@example.com", username="caller", hashed_password="pass")
        receiver = User(email="receiver@example.com", username="receiver", hashed_password="pass")
        db_session.add(caller)
        db_session.add(receiver)
        db_session.commit()

        call = Call(
            caller_id=caller.id,
            receiver_id=receiver.id,
            call_type="voice",
            status="initiated",
            start_time=datetime.utcnow(),
            duration=0,
            dropped_calls=0,
        )
        db_session.add(call)
        db_session.commit()

        assert call.id is not None
        assert call.caller_id == caller.id
        assert call.receiver_id == receiver.id
        assert call.call_type == "voice"
        assert call.status == "initiated"

    def test_call_repr(self, db_session):
        """Test string representation of call"""
        call = Call(
            caller_id=1,
            receiver_id=2,
            call_type="video",
            status="ongoing",
        )
        expected = f"<Call(id={call.id}, caller_id={call.caller_id}, receiver_id={call.receiver_id}, status='{call.status}')>"
        assert repr(call) == expected


class TestWebRTCSessionModel:
    """Test cases for WebRTCSession model"""

    def test_webrtc_session_creation(self, db_session):
        """Test creating a WebRTC session"""
        call = db_session.query(Call).first()
        session = WebRTCSession(
            call_id=call.id,
            offer="offer_sdp",
            answer="answer_sdp",
            ice_candidates='["candidate1", "candidate2"]',
            connection_quality="good",
        )
        db_session.add(session)
        db_session.commit()

        assert session.id is not None
        assert session.call_id == call.id
        assert session.connection_quality == "good"

    def test_webrtc_session_repr(self, db_session):
        """Test string representation of WebRTC session"""
        session = WebRTCSession(
            call_id=1,
            offer="offer",
            answer="answer",
        )
        expected = f"<WebRTCSession(id={session.id}, call_id={session.call_id})>"
        assert repr(session) == expected


if __name__ == "__main__":
    pytest.main([__file__])
