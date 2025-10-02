#!/usr/bin/env python3
"""
Phone Number Models for Namaskah Platform

This module defines SQLAlchemy models for phone number management, including
available numbers, ownership, usage tracking, and related API models.
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKey, Index,
                        Integer, Numeric, String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


# Enums
class PhoneNumberStatus(str, enum.Enum):
    """Enumeration of phone number statuses"""
    AVAILABLE = "available"
    PURCHASED = "purchased"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PhoneNumberProvider(str, enum.Enum):
    """Enumeration of phone number providers"""
    TWILIO = "twilio"
    TEXTVERIFIED = "textverified"
    MOCK = "mock"  # For development/testing


class PhoneNumberCapability(str, enum.Enum):
    """Enumeration of phone number capabilities"""
    SMS = "sms"
    VOICE = "voice"
    MMS = "mms"
    FAX = "fax"


# SQLAlchemy Models
class PhoneNumber(Base):
    """
    Phone numbers available for purchase or owned by users.

    Manages phone number inventory, ownership, pricing, capabilities, and usage tracking.
    """

    __tablename__ = "phone_numbers"
    __table_args__ = (
        CheckConstraint('total_sms_sent >= 0', name='check_total_sms_sent_non_negative'),
        CheckConstraint('total_sms_received >= 0', name='check_total_sms_received_non_negative'),
        CheckConstraint('total_voice_minutes >= 0', name='check_total_voice_minutes_non_negative'),
        CheckConstraint('monthly_sms_sent >= 0', name='check_monthly_sms_sent_non_negative'),
        CheckConstraint('monthly_voice_minutes >= 0', name='check_monthly_voice_minutes_non_negative'),
        Index("idx_phone_number_status", "status"),
        Index("idx_phone_number_country", "country_code"),
        Index("idx_phone_number_owner", "owner_id"),
        Index("idx_phone_number_provider", "provider"),
        Index("idx_phone_number_expires", "expires_at"),
        {"extend_existing": True},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(20), unique=True, nullable=False, index=True)

    # Provider information
    provider = Column(Enum(PhoneNumberProvider), nullable=False)
    provider_id = Column(String(255))  # Provider's internal ID
    country_code = Column(String(3), nullable=False)
    area_code = Column(String(10))
    region = Column(String(100))

    # Ownership and status
    owner_id = Column(String(36), ForeignKey("users.id"))
    status = Column(Enum(PhoneNumberStatus), default=PhoneNumberStatus.AVAILABLE, nullable=False)

    # Pricing
    monthly_cost = Column(Numeric(10, 2))  # Monthly subscription cost
    sms_cost_per_message = Column(Numeric(10, 4))  # Cost per SMS
    voice_cost_per_minute = Column(Numeric(10, 4))  # Cost per voice minute
    setup_fee = Column(Numeric(10, 2), default=0, nullable=False)

    # Capabilities
    capabilities = Column(Text)  # JSON array of capabilities

    # Usage tracking
    total_sms_sent = Column(Integer, default=0, nullable=False)
    total_sms_received = Column(Integer, default=0, nullable=False)
    total_voice_minutes = Column(Integer, default=0, nullable=False)
    monthly_sms_sent = Column(Integer, default=0, nullable=False)
    monthly_voice_minutes = Column(Integer, default=0, nullable=False)

    # Subscription details
    purchased_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    auto_renew = Column(Boolean, default=True, nullable=False)
    last_renewal_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="phone_numbers")

    def __repr__(self):
        return f"<PhoneNumber(id='{self.id}', number='{self.phone_number}', status={self.status.value}, provider={self.provider.value})>"


class PhoneNumberUsage(Base):
    """
    Daily usage tracking for phone numbers.

    Records daily usage metrics and costs for billing and analytics purposes.
    """

    __tablename__ = "phone_number_usage"
    __table_args__ = (
        CheckConstraint('sms_sent >= 0', name='check_sms_sent_non_negative'),
        CheckConstraint('sms_received >= 0', name='check_sms_received_non_negative'),
        CheckConstraint('voice_minutes >= 0', name='check_voice_minutes_non_negative'),
        CheckConstraint('sms_cost >= 0', name='check_sms_cost_non_negative'),
        CheckConstraint('voice_cost >= 0', name='check_voice_cost_non_negative'),
        CheckConstraint('total_cost >= 0', name='check_total_cost_non_negative'),
        Index("idx_usage_phone_date", "phone_number_id", "usage_date"),
        Index("idx_usage_user_date", "user_id", "usage_date"),
        {"extend_existing": True},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number_id = Column(String(36), ForeignKey("phone_numbers.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Usage date
    usage_date = Column(DateTime(timezone=True), nullable=False, index=True)

    # Usage metrics
    sms_sent = Column(Integer, default=0, nullable=False)
    sms_received = Column(Integer, default=0, nullable=False)
    voice_minutes = Column(Integer, default=0, nullable=False)

    # Costs
    sms_cost = Column(Numeric(10, 4), default=0, nullable=False)
    voice_cost = Column(Numeric(10, 4), default=0, nullable=False)
    total_cost = Column(Numeric(10, 4), default=0, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    phone_number = relationship("PhoneNumber")
    user = relationship("User")

    def __repr__(self):
        return f"<PhoneNumberUsage(id='{self.id}', phone_number_id='{self.phone_number_id}', date='{self.usage_date}', total_cost={self.total_cost})>"


# Pydantic Models for API
class PhoneNumberSearch(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=3)
    area_code: Optional[str] = None
    capabilities: List[PhoneNumberCapability] = Field(
        default_factory=lambda: [PhoneNumberCapability.SMS]
    )
    limit: int = Field(default=20, ge=1, le=100)


class AvailablePhoneNumber(BaseModel):
    phone_number: str
    country_code: str
    area_code: Optional[str]
    region: Optional[str]
    provider: PhoneNumberProvider
    monthly_cost: Decimal
    sms_cost_per_message: Decimal
    voice_cost_per_minute: Optional[Decimal]
    setup_fee: Decimal
    capabilities: List[PhoneNumberCapability]

    class Config:
        from_attributes = True


class PhoneNumberPurchase(BaseModel):
    phone_number: str
    auto_renew: bool = True


class OwnedPhoneNumber(BaseModel):
    id: str
    phone_number: str
    country_code: str
    area_code: Optional[str]
    region: Optional[str]
    provider: PhoneNumberProvider
    status: PhoneNumberStatus
    monthly_cost: Decimal
    purchased_at: datetime
    expires_at: datetime
    auto_renew: bool

    # Usage statistics
    total_sms_sent: int
    total_sms_received: int
    total_voice_minutes: int
    monthly_sms_sent: int
    monthly_voice_minutes: int

    class Config:
        from_attributes = True


class PhoneNumberUsageStats(BaseModel):
    phone_number_id: str
    phone_number: str
    period_start: datetime
    period_end: datetime

    # Usage metrics
    total_sms_sent: int
    total_sms_received: int
    total_voice_minutes: int

    # Cost breakdown
    sms_cost: Decimal
    voice_cost: Decimal
    monthly_fee: Decimal
    total_cost: Decimal

    # Daily breakdown
    daily_usage: List[dict] = Field(default_factory=list)


class PhoneNumberRenewal(BaseModel):
    phone_number_id: str
    renewal_period_months: int = Field(default=1, ge=1, le=12)
    auto_renew: Optional[bool] = None


class PhoneNumberResponse(BaseModel):
    success: bool
    message: str
    phone_number: Optional[OwnedPhoneNumber] = None
    transaction_id: Optional[str] = None


class PhoneNumberListResponse(BaseModel):
    phone_numbers: List[AvailablePhoneNumber]
    total_count: int
    country_code: str
    area_code: Optional[str]


class OwnedPhoneNumberListResponse(BaseModel):
    phone_numbers: List[OwnedPhoneNumber]
    total_count: int
    active_count: int
    total_monthly_cost: Decimal
