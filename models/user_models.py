#!/usr/bin/env python3
"""
User Management Models for Namaskah Communication Platform

This module defines SQLAlchemy models for user management, sessions, and API keys,
along with Pydantic models for API request/response validation.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer,
                        String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class UserRole(str, Enum):
    """Enumeration of user roles in the system"""
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"


class SubscriptionPlan(str, Enum):
    """Enumeration of available subscription plans"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class User(Base):
    """
    User model for the communication platform.

    Represents a registered user with authentication, subscription, and usage tracking.
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint('monthly_sms_used >= 0', name='check_sms_used_non_negative'),
        CheckConstraint('monthly_voice_minutes_used >= 0', name='check_voice_used_non_negative'),
        CheckConstraint('api_calls_today >= 0', name='check_api_calls_non_negative'),
        Index('ix_users_email_active', 'email', 'is_active'),
        Index('ix_users_username_active', 'username', 'is_active'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(20), default=UserRole.USER.value, nullable=False)

    # Subscription info
    subscription_plan = Column(String(20), default=SubscriptionPlan.FREE.value, nullable=False)
    subscription_expires = Column(DateTime(timezone=True))

    # Usage limits
    monthly_sms_limit = Column(Integer, default=100, nullable=False)
    monthly_sms_used = Column(Integer, default=0, nullable=False)
    monthly_voice_minutes_limit = Column(Integer, default=60, nullable=False)
    monthly_voice_minutes_used = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # API access (deprecated - use APIKey model instead)
    api_calls_today = Column(Integer, default=0, nullable=False)
    api_rate_limit = Column(Integer, default=1000, nullable=False)

    # Email verification
    email_verification_token = Column(String(255))
    email_verification_expires = Column(DateTime(timezone=True))

    # Password reset
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime(timezone=True))
    
    # Email verification timestamp
    email_verified_at = Column(DateTime(timezone=True))

    # Relationships
    owned_numbers = relationship("PhoneNumber", back_populates="owner")
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    verification_requests = relationship("VerificationRequest", back_populates="user")
    user_numbers = relationship(
        "UserNumber", back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions = relationship("UserSubscription", back_populates="user")
    email_tokens = relationship("EmailVerificationToken", back_populates="user")

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}', active={self.is_active})>"


class Session(Base):
    """
    User sessions for JWT refresh token management.

    Tracks active user sessions for authentication and security monitoring.
    """

    __tablename__ = "sessions"
    __table_args__ = (
        Index("idx_session_refresh_token", "refresh_token"),
        Index("idx_session_user_active", "user_id", "is_active"),
        Index("idx_session_expires_at", "expires_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), server_default=func.now())
    user_agent = Column(String(255))
    ip_address = Column(String(45))  # IPv6 addresses can be up to 45 chars
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session(id='{self.id}', user_id='{self.user_id}', active={self.is_active})>"


class APIKey(Base):
    """
    API keys for programmatic access.

    Manages API keys with usage tracking, scopes, and expiration.
    """

    __tablename__ = "api_keys"
    __table_args__ = (
        CheckConstraint('total_requests >= 0', name='check_total_requests_non_negative'),
        CheckConstraint('requests_today >= 0', name='check_requests_today_non_negative'),
        Index("idx_apikey_hash", "key_hash"),
        Index("idx_apikey_user_active", "user_id", "is_active"),
        Index("idx_apikey_expires_at", "expires_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    scopes = Column(Text)  # JSON array of permissions
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Usage tracking
    total_requests = Column(Integer, default=0, nullable=False)
    requests_today = Column(Integer, default=0, nullable=False)
    last_request_date = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id='{self.id}', name='{self.name}', user_id='{self.user_id}', active={self.is_active})>"


# Pydantic models for API
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    subscription_plan: SubscriptionPlan
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    name: str
    scopes: Optional[str] = None
    expires_in_days: Optional[int] = 365  # Default to 1 year


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str  # First 8 chars of the key
    scopes: Optional[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


class APIKeyRevoke(BaseModel):
    id: str
