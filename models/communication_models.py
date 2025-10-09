#!/usr/bin/env python3
"""
Communication Models for namaskah Communication Platform
Enhanced models for SMS, voice, and communication management
"""
import enum
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy import (JSON, Boolean, Column, DateTime, Enum, ForeignKey,
                        Index, Integer, Numeric, String, Text)
from sqlalchemy.orm import relationship

from core.database import Base


# Enums
class MessageDirection(enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(enum.Enum):
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNDELIVERED = "undelivered"


class CallStatus(enum.Enum):
    QUEUED = "queued"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    BUSY = "busy"
    NO_ANSWER = "no-answer"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommunicationType(enum.Enum):
    SMS = "sms"
    MMS = "mms"
    VOICE = "voice"
    CONFERENCE = "conference"


class RoutingStrategy(enum.Enum):
    DIRECT = "direct"
    SMART_ROUTING = "smart_routing"
    COST_OPTIMIZED = "cost_optimized"
    DELIVERY_OPTIMIZED = "delivery_optimized"


# SQLAlchemy Models
class CommunicationSession(Base):
    """Communication sessions for tracking related messages/calls"""

    __tablename__ = "communication_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Session details
    session_type = Column(Enum(CommunicationType), nullable=False)
    external_number = Column(String(20), nullable=False)
    from_number = Column(String(20), nullable=False)

    # Session metadata
    title = Column(String(200))
    description = Column(Text)

    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    messages = relationship("CommunicationMessage", back_populates="session")
    calls = relationship("VoiceCall", back_populates="session")

    # Indexes
    __table_args__ = (
        Index("idx_session_user", "user_id"),
        Index("idx_session_external_number", "external_number"),
        Index("idx_session_type", "session_type"),
        Index("idx_session_active", "is_active"),
        Index("idx_session_last_activity", "last_activity_at"),
        {"extend_existing": True},
    )


class CommunicationMessage(Base):
    """Enhanced message model for SMS/MMS communication"""

    __tablename__ = "communication_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("communication_sessions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Message details
    direction = Column(Enum(MessageDirection), nullable=False)
    message_type = Column(Enum(CommunicationType), default=CommunicationType.SMS)
    content = Column(Text, nullable=False)

    # Phone numbers
    from_number = Column(String(20), nullable=False)
    to_number = Column(String(20), nullable=False)

    # Provider details
    provider = Column(String(50), default="twilio")
    provider_message_id = Column(String(200))  # Twilio SID, etc.

    # Status and delivery
    status = Column(Enum(MessageStatus), default=MessageStatus.QUEUED)
    delivery_status = Column(String(50))
    error_code = Column(String(20))
    error_message = Column(Text)

    # Routing information
    routing_strategy = Column(Enum(RoutingStrategy), default=RoutingStrategy.DIRECT)
    routing_info = Column(JSON)  # Routing decisions and metadata

    # Pricing
    cost = Column(Numeric(10, 4))
    currency = Column(String(3), default="USD")

    # Media (for MMS)
    media_urls = Column(JSON)  # Array of media URLs
    media_count = Column(Integer, default=0)

    # AI assistance
    ai_suggested = Column(Boolean, default=False)
    ai_confidence = Column(Numeric(5, 4))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)

    # Relationships
    session = relationship("CommunicationSession", back_populates="messages")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_message_session", "session_id"),
        Index("idx_message_user", "user_id"),
        Index("idx_message_direction", "direction"),
        Index("idx_message_status", "status"),
        Index("idx_message_provider_id", "provider_message_id"),
        Index("idx_message_created", "created_at"),
        Index("idx_message_numbers", "from_number", "to_number"),
        {"extend_existing": True},
    )


class VoiceCall(Base):
    """Voice call records"""

    __tablename__ = "voice_calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("communication_sessions.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Call details
    direction = Column(Enum(MessageDirection), nullable=False)
    from_number = Column(String(20), nullable=False)
    to_number = Column(String(20), nullable=False)

    # Provider details
    provider = Column(String(50), default="twilio")
    provider_call_id = Column(String(200))  # Twilio Call SID

    # Call status and duration
    status = Column(Enum(CallStatus), default=CallStatus.QUEUED)
    duration = Column(Integer, default=0)  # Duration in seconds

    # Routing information
    routing_strategy = Column(Enum(RoutingStrategy), default=RoutingStrategy.DIRECT)
    routing_info = Column(JSON)

    # Recording
    is_recorded = Column(Boolean, default=False)
    recording_url = Column(String(500))
    recording_duration = Column(Integer)

    # Conference details
    conference_id = Column(String, ForeignKey("conference_calls.id"))
    is_conference_call = Column(Boolean, default=False)

    # Pricing
    cost = Column(Numeric(10, 4))
    currency = Column(String(3), default="USD")

    # Call quality metrics
    quality_score = Column(Numeric(3, 2))  # 1.0 to 5.0

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    answered_at = Column(DateTime)
    ended_at = Column(DateTime)

    # Relationships
    session = relationship("CommunicationSession", back_populates="calls")
    user = relationship("User")
    conference = relationship("ConferenceCall", back_populates="participants")

    # Indexes
    __table_args__ = (
        Index("idx_call_session", "session_id"),
        Index("idx_call_user", "user_id"),
        Index("idx_call_direction", "direction"),
        Index("idx_call_status", "status"),
        Index("idx_call_provider_id", "provider_call_id"),
        Index("idx_call_created", "created_at"),
        Index("idx_call_conference", "conference_id"),
        {"extend_existing": True},
    )


class ConferenceCall(Base):
    """Conference call management"""

    __tablename__ = "conference_calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False
    )  # Conference creator

    # Conference details
    conference_name = Column(String(200), nullable=False)
    friendly_name = Column(String(200))

    # Provider details
    provider = Column(String(50), default="twilio")
    provider_conference_id = Column(String(200))  # Twilio Conference SID

    # Configuration
    max_participants = Column(Integer, default=10)
    is_recorded = Column(Boolean, default=False)
    recording_url = Column(String(500))

    # Status
    status = Column(String(50), default="created")  # created, active, completed
    participant_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)

    # Relationships
    creator = relationship("User")
    participants = relationship("VoiceCall", back_populates="conference")

    # Indexes
    __table_args__ = (
        Index("idx_conference_user", "user_id"),
        Index("idx_conference_name", "conference_name"),
        Index("idx_conference_provider_id", "provider_conference_id"),
        Index("idx_conference_status", "status"),
        Index("idx_conference_created", "created_at"),
        {"extend_existing": True},
    )


class CommunicationAnalytics(Base):
    """Analytics for communication usage"""

    __tablename__ = "communication_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly

    # User and number
    user_id = Column(String, ForeignKey("users.id"))
    phone_number = Column(String(20))
    country_code = Column(String(3))

    # Message metrics
    sms_sent = Column(Integer, default=0)
    sms_received = Column(Integer, default=0)
    sms_delivered = Column(Integer, default=0)
    sms_failed = Column(Integer, default=0)

    # Voice metrics
    calls_made = Column(Integer, default=0)
    calls_received = Column(Integer, default=0)
    calls_completed = Column(Integer, default=0)
    total_call_duration = Column(Integer, default=0)  # Seconds

    # Cost metrics
    sms_cost = Column(Numeric(10, 4), default=0)
    voice_cost = Column(Numeric(10, 4), default=0)
    total_cost = Column(Numeric(10, 4), default=0)

    # Quality metrics
    average_delivery_time = Column(Integer)  # Seconds
    delivery_success_rate = Column(Numeric(5, 4))
    call_success_rate = Column(Numeric(5, 4))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_comm_analytics_date", "date"),
        Index("idx_comm_analytics_user_date", "user_id", "date"),
        Index("idx_comm_analytics_number_date", "phone_number", "date"),
        Index("idx_comm_analytics_country_date", "country_code", "date"),
        {"extend_existing": True},
    )


# Pydantic Models for API
class CommunicationSessionResponse(BaseModel):
    """Response model for communication session"""

    id: str
    user_id: str
    session_type: CommunicationType
    external_number: str
    from_number: str
    title: Optional[str]
    description: Optional[str]
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime
    message_count: int = 0
    call_count: int = 0

    class Config:
        from_attributes = True


class MessageCreateRequest(BaseModel):
    """Request model for creating a message"""

    to_number: str = Field(..., description="Recipient phone number")
    content: str = Field(..., description="Message content", max_length=1600)
    from_number: Optional[str] = Field(None, description="Sender phone number")
    message_type: CommunicationType = CommunicationType.SMS
    use_smart_routing: bool = True
    routing_strategy: RoutingStrategy = RoutingStrategy.SMART_ROUTING
    media_urls: Optional[List[str]] = Field(None, description="Media URLs for MMS")

    @validator("to_number", "from_number")
    def validate_phone_numbers(cls, v):
        if v and not v.startswith("+"):
            raise ValueError("Phone number must be in E.164 format")
        return v

    @validator("content")
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Message content cannot be empty")
        return v.strip()


class MessageResponse(BaseModel):
    """Response model for message details"""

    id: str
    session_id: str
    user_id: str
    direction: MessageDirection
    message_type: CommunicationType
    content: str
    from_number: str
    to_number: str
    provider: str
    provider_message_id: Optional[str]
    status: MessageStatus
    delivery_status: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    routing_strategy: RoutingStrategy
    routing_info: Optional[Dict[str, Any]]
    cost: Optional[Decimal]
    currency: str
    media_urls: Optional[List[str]]
    media_count: int
    ai_suggested: bool
    ai_confidence: Optional[Decimal]
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]

    class Config:
        from_attributes = True


class CallCreateRequest(BaseModel):
    """Request model for creating a voice call"""

    to_number: str = Field(..., description="Recipient phone number")
    from_number: Optional[str] = Field(None, description="Caller phone number")
    use_smart_routing: bool = True
    routing_strategy: RoutingStrategy = RoutingStrategy.SMART_ROUTING
    record_call: bool = False
    twiml_url: Optional[str] = Field(
        None, description="TwiML URL for call instructions"
    )

    @validator("to_number", "from_number")
    def validate_phone_numbers(cls, v):
        if v and not v.startswith("+"):
            raise ValueError("Phone number must be in E.164 format")
        return v


class CallResponse(BaseModel):
    """Response model for voice call details"""

    id: str
    session_id: Optional[str]
    user_id: str
    direction: MessageDirection
    from_number: str
    to_number: str
    provider: str
    provider_call_id: Optional[str]
    status: CallStatus
    duration: int
    routing_strategy: RoutingStrategy
    routing_info: Optional[Dict[str, Any]]
    is_recorded: bool
    recording_url: Optional[str]
    recording_duration: Optional[int]
    conference_id: Optional[str]
    is_conference_call: bool
    cost: Optional[Decimal]
    currency: str
    quality_score: Optional[Decimal]
    created_at: datetime
    started_at: Optional[datetime]
    answered_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConferenceCreateRequest(BaseModel):
    """Request model for creating a conference call"""

    conference_name: str = Field(..., description="Conference name")
    friendly_name: Optional[str] = Field(None, description="Friendly conference name")
    participants: List[str] = Field(..., description="Participant phone numbers")
    max_participants: int = Field(10, ge=2, le=50)
    record_conference: bool = False

    @validator("participants")
    def validate_participants(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 participants required")
        for number in v:
            if not number.startswith("+"):
                raise ValueError(f"Invalid phone number format: {number}")
        return v


class ConferenceResponse(BaseModel):
    """Response model for conference call details"""

    id: str
    user_id: str
    conference_name: str
    friendly_name: Optional[str]
    provider: str
    provider_conference_id: Optional[str]
    max_participants: int
    is_recorded: bool
    recording_url: Optional[str]
    status: str
    participant_count: int
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class CommunicationStatsResponse(BaseModel):
    """Response model for communication statistics"""

    user_id: str
    period_start: datetime
    period_end: datetime

    # Message statistics
    total_messages_sent: int
    total_messages_received: int
    messages_delivered: int
    messages_failed: int
    message_delivery_rate: float

    # Call statistics
    total_calls_made: int
    total_calls_received: int
    calls_completed: int
    total_call_duration: int
    call_success_rate: float

    # Cost statistics
    total_sms_cost: Decimal
    total_voice_cost: Decimal
    total_cost: Decimal

    # Usage by country
    usage_by_country: Dict[str, int]
    cost_by_country: Dict[str, Decimal]


class MessageFilters(BaseModel):
    """Filters for message queries"""

    session_id: Optional[str] = None
    direction: Optional[MessageDirection] = None
    message_type: Optional[CommunicationType] = None
    status: Optional[MessageStatus] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_content: Optional[str] = None


class CallFilters(BaseModel):
    """Filters for call queries"""

    session_id: Optional[str] = None
    direction: Optional[MessageDirection] = None
    status: Optional[CallStatus] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_duration: Optional[int] = None
    is_recorded: Optional[bool] = None
