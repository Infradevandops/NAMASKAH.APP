#!/usr/bin/env python3
"""
Verification Models for Namaskah Communication Platform

Enhanced models for TextVerified integration and verification management.
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy import (JSON, Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKey,
                        Index, Integer, Numeric, String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


# Enums
class VerificationStatus(str, enum.Enum):
    """Enumeration of verification request statuses"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class VerificationProvider(str, enum.Enum):
    """Enumeration of verification service providers"""
    TEXTVERIFIED = "textverified"
    TWILIO = "twilio"
    MOCK = "mock"


class ServiceCategory(str, enum.Enum):
    """Enumeration of service categories"""
    SOCIAL = "social"
    MESSAGING = "messaging"
    TECH = "tech"
    GAMING = "gaming"
    FINANCE = "finance"
    ECOMMERCE = "ecommerce"
    OTHER = "other"


# SQLAlchemy Models
class VerificationService(Base):
    """
    Supported verification services configuration.

    Defines available verification services, pricing, and metadata.
    """

    __tablename__ = "verification_services"
    __table_args__ = (
        Index("idx_service_name", "service_name"),
        Index("idx_service_category", "category"),
        Index("idx_service_active", "is_active"),
        Index("idx_service_provider", "provider"),
        {"extend_existing": True},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    category = Column(Enum(ServiceCategory), nullable=False)

    # Service configuration
    is_active = Column(Boolean, default=True, nullable=False)
    provider = Column(
        Enum(VerificationProvider), default=VerificationProvider.TEXTVERIFIED, nullable=False
    )
    provider_service_id = Column(String(100))  # Provider's internal service ID

    # Pricing and limits
    base_cost = Column(Numeric(10, 4), default=0, nullable=False)
    success_rate = Column(Numeric(5, 4), default=0.95, nullable=False)  # Expected success rate
    average_delivery_time = Column(Integer, default=30, nullable=False)  # Seconds

    # Service metadata
    description = Column(Text)
    logo_url = Column(String(500))
    website_url = Column(String(500))
    supported_countries = Column(JSON)  # List of supported country codes

    # Code patterns for extraction
    code_patterns = Column(JSON)  # Regex patterns for code extraction
    typical_code_length = Column(Integer, default=6, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    verification_requests = relationship(
        "VerificationRequest", back_populates="service"
    )


class VerificationRequest(Base):
    """Individual verification requests"""

    __tablename__ = "verification_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    service_id = Column(String, ForeignKey("verification_services.id"), nullable=False)

    # Provider details
    provider = Column(Enum(VerificationProvider), nullable=False)
    provider_request_id = Column(String(200))  # TextVerified ID, etc.

    # Phone number details
    phone_number = Column(String(20))
    country_code = Column(String(3))

    # Status and progress
    status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    verification_code = Column(String(20))

    # Smart routing information
    routing_info = Column(JSON)  # Routing decisions and metadata
    cost_estimate = Column(Numeric(10, 4))
    actual_cost = Column(Numeric(10, 4))

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(
        DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=30)
    )
    completed_at = Column(DateTime)

    # Retry information
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_retry_at = Column(DateTime)

    # Messages and codes
    received_messages = Column(JSON)  # Array of received SMS messages
    extracted_codes = Column(JSON)  # Array of extracted verification codes
    auto_completed = Column(Boolean, default=False)

    # Metadata
    priority = Column(String(20), default="normal")  # low, normal, high
    request_metadata = Column(JSON)  # Additional request metadata

    # Relationships
    user = relationship("User", back_populates="verification_requests")
    service = relationship(
        "VerificationService", back_populates="verification_requests"
    )

    # Indexes
    __table_args__ = (
        Index("idx_verification_user", "user_id"),
        Index("idx_verification_service", "service_id"),
        Index("idx_verification_status", "status"),
        Index("idx_verification_provider_id", "provider_request_id"),
        Index("idx_verification_created", "created_at"),
        Index("idx_verification_expires", "expires_at"),
        {"extend_existing": True},
    )


class VerificationMessage(Base):
    """SMS messages received during verification"""

    __tablename__ = "verification_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_id = Column(
        String, ForeignKey("verification_requests.id"), nullable=False
    )

    # Message details
    message_content = Column(Text, nullable=False)
    sender_number = Column(String(20))
    received_at = Column(DateTime, default=datetime.utcnow)

    # Code extraction
    extracted_codes = Column(JSON)  # Codes found in this message
    extraction_confidence = Column(Numeric(5, 4))  # Confidence score

    # Provider details
    provider_message_id = Column(String(200))

    message_metadata = Column(JSON)  # Additional message metadata

    # Relationships
    verification = relationship("VerificationRequest")

    # Indexes
    __table_args__ = (
        Index("idx_message_verification", "verification_id"),
        Index("idx_message_received", "received_at"),
        {"extend_existing": True},
    )


class VerificationAnalytics(Base):
    """Analytics data for verification performance"""

    __tablename__ = "verification_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly

    # Service and user
    service_id = Column(String, ForeignKey("verification_services.id"))
    user_id = Column(String, ForeignKey("users.id"))
    country_code = Column(String(3))

    # Metrics
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    cancelled_requests = Column(Integer, default=0)

    # Performance metrics
    average_completion_time = Column(Integer)  # Seconds
    success_rate = Column(Numeric(5, 4))
    total_cost = Column(Numeric(10, 4))
    average_cost = Column(Numeric(10, 4))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("VerificationService")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_analytics_date", "date"),
        Index("idx_analytics_service_date", "service_id", "date"),
        Index("idx_analytics_user_date", "user_id", "date"),
        Index("idx_analytics_country_date", "country_code", "date"),
        {"extend_existing": True},
    )


# Pydantic Models for API
class VerificationServiceResponse(BaseModel):
    """Response model for verification service information"""

    id: str
    service_name: str
    display_name: str
    category: ServiceCategory
    is_active: bool
    provider: VerificationProvider
    base_cost: Decimal
    success_rate: Decimal
    average_delivery_time: int
    description: Optional[str]
    logo_url: Optional[str]
    supported_countries: Optional[List[str]]
    typical_code_length: int

    class Config:
        from_attributes = True


class VerificationRequestCreate(BaseModel):
    """Request model for creating verification"""

    service_name: str
    capability: str = "sms"
    country_preference: Optional[str] = None
    use_smart_routing: bool = True
    priority: str = "normal"

    @validator("service_name")
    def validate_service_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Service name cannot be empty")
        return v.lower().strip()

    @validator("priority")
    def validate_priority(cls, v):
        valid_priorities = ["low", "normal", "high"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v


class VerificationRequestResponse(BaseModel):
    """Response model for verification request"""

    id: str
    user_id: str
    service_name: str
    service_display_name: str
    provider: VerificationProvider
    phone_number: Optional[str]
    country_code: Optional[str]
    status: VerificationStatus
    verification_code: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    completed_at: Optional[datetime]
    retry_count: int
    max_retries: int
    cost_estimate: Optional[Decimal]
    actual_cost: Optional[Decimal]
    routing_info: Optional[Dict[str, Any]]
    auto_completed: bool
    priority: str

    class Config:
        from_attributes = True


class VerificationMessagesResponse(BaseModel):
    """Response model for verification messages"""

    verification_id: str
    messages: List[Dict[str, Any]]
    extracted_codes: List[str]
    auto_completed: bool
    last_checked: datetime
    next_check_in: Optional[int]


class VerificationStatsResponse(BaseModel):
    """Response model for verification statistics"""

    period_days: int
    total_verifications: int
    completed_verifications: int
    success_rate: float
    average_completion_time: Optional[float]
    status_breakdown: Dict[str, int]
    service_breakdown: Dict[str, int]
    country_breakdown: Dict[str, int]
    cost_summary: Dict[str, float]


class VerificationRetryRequest(BaseModel):
    """Request model for retrying verification"""

    use_different_number: bool = False
    country_preference: Optional[str] = None


class BulkVerificationRequest(BaseModel):
    """Request model for bulk verification creation"""

    services: List[str] = Field(..., min_items=1, max_items=10)
    capability: str = "sms"
    country_preference: Optional[str] = None
    use_smart_routing: bool = True
    stagger_delay: int = Field(5, ge=0, le=60)

    @validator("services")
    def validate_services(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one service is required")
        return [service.lower().strip() for service in v]


class VerificationAnalyticsResponse(BaseModel):
    """Response model for verification analytics"""

    date: datetime
    period_type: str
    service_name: Optional[str]
    country_code: Optional[str]
    total_requests: int
    successful_requests: int
    failed_requests: int
    cancelled_requests: int
    success_rate: Decimal
    average_completion_time: Optional[int]
    total_cost: Decimal
    average_cost: Decimal


class VerificationExportRequest(BaseModel):
    """Request model for verification data export"""

    format_type: str = Field("json", pattern="^(json|csv)$")
    service_name: Optional[str] = None
    status: Optional[VerificationStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_messages: bool = False
    include_analytics: bool = False
