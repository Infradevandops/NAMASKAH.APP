#!/usr/bin/env python3
"""
Refresh Token Models for Auth 2.0
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional, Dict, Any

Base = declarative_base()

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    device_info = Column(JSON, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="refresh_tokens")
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_revoked(self) -> bool:
        """Check if token is revoked"""
        return self.revoked_at is not None
    
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_expired() and not self.is_revoked() and self.is_active

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_jti = Column(String(255), nullable=False, unique=True)  # JWT ID
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    reason = Column(String(100), nullable=True)  # logout, security, etc.

# Pydantic models for API
class RefreshTokenCreate(BaseModel):
    user_id: str
    device_info: Optional[Dict[str, Any]] = None

class RefreshTokenResponse(BaseModel):
    id: str
    expires_at: datetime
    created_at: datetime
    device_info: Optional[Dict[str, Any]] = None
    is_active: bool

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class LogoutRequest(BaseModel):
    refresh_token: str

class LogoutAllRequest(BaseModel):
    user_id: str