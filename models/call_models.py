from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    call_type = Column(String(10), nullable=False)  # 'voice' or 'video'
    status = Column(String(20), nullable=False)  # 'initiated', 'ongoing', 'ended'
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds

    caller = relationship("User", foreign_keys=[caller_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

    # Additional metadata
    call_sid = Column(String(100), nullable=True)  # External service call ID
    recording_url = Column(String(500), nullable=True)
    transcription_url = Column(String(500), nullable=True)

    # Quality metrics
    quality_score = Column(Integer, nullable=True)  # 1-5 rating
    dropped_calls = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    webrtc_session = relationship("WebRTCSession", back_populates="call", uselist=False)

    def __repr__(self):
        return f"<Call(id={self.id}, caller_id={self.caller_id}, receiver_id={self.receiver_id}, status='{self.status}')>"


class WebRTCSession(Base):
    __tablename__ = "webrtc_sessions"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"), nullable=False, index=True, unique=True)
    offer = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    ice_candidates = Column(Text, nullable=True)  # JSON string

    session_started_at = Column(DateTime(timezone=True), server_default=func.now())
    session_ended_at = Column(DateTime(timezone=True), nullable=True)

    connection_quality = Column(String(20), nullable=True)  # 'excellent', 'good', 'poor'

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    call = relationship("Call", back_populates="webrtc_session")

    def __repr__(self):
        return f"<WebRTCSession(id={self.id}, call_id={self.call_id})>"
