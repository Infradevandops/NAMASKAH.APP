#!/usr/bin/env python3
"""
Enhanced Conversation and Message Models for Namaskah Platform

This module defines SQLAlchemy models for conversations, messages, and related
functionality including participant management and message threading.
"""
import enum
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Index,
                        Integer, String, Table, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


# Enums
class ConversationStatus(str, enum.Enum):
    """Enumeration of conversation statuses"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    BLOCKED = "blocked"


class MessageType(str, enum.Enum):
    """Enumeration of message types"""
    CHAT = "chat"  # Internal chat messages
    SMS_OUTBOUND = "sms_outbound"  # SMS sent to external number
    SMS_INBOUND = "sms_inbound"  # SMS received from external number
    SYSTEM = "system"  # System notifications
    INTERNAL = "internal"  # Legacy support


# Association table for conversation participants
conversation_participants = Table(
    "conversation_participants",
    Base.metadata,
    Column("conversation_id", String(36), ForeignKey("conversations.id"), primary_key=True, index=True),
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True, index=True),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("last_read_at", DateTime(timezone=True), server_default=func.now()),
    Column("is_admin", Boolean, default=False, nullable=False),
    Column("notifications_enabled", Boolean, default=True, nullable=False),
    extend_existing=True,
)


# SQLAlchemy Models
class Conversation(Base):
    """
    Model for conversations (chats) in the platform.

    Represents both individual and group conversations, including SMS-based
    conversations with external numbers.
    """

    __tablename__ = "conversations"
    __table_args__ = (
        Index("idx_conversation_status", "status"),
        Index("idx_conversation_created_by", "created_by"),
        Index("idx_conversation_last_message", "last_message_at"),
        Index("idx_conversation_external_number", "external_number"),
        {"extend_existing": True},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255))
    is_group = Column(Boolean, default=False, nullable=False)
    external_number = Column(String(20))
    status = Column(
        Enum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False
    )

    # Metadata
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True))

    # Settings
    is_archived = Column(Boolean, default=False, nullable=False)
    is_muted = Column(Boolean, default=False, nullable=False)

    # Relationships
    participants = relationship(
        "User", secondary=conversation_participants, back_populates="conversations"
    )
    messages = relationship(
        "Message",
        back_populates="conversation",
        order_by="Message.created_at",
        cascade="all, delete-orphan",
    )
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Conversation(id='{self.id}', title='{self.title}', status={self.status.value}, group={self.is_group})>"


class Message(Base):
    """
    Model for messages within conversations.

    Supports various message types including chat, SMS, system notifications,
    and tracks delivery and read status.
    """

    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_message_conversation", "conversation_id"),
        Index("idx_message_sender", "sender_id"),
        Index("idx_message_created_at", "created_at"),
        Index("idx_message_type", "message_type"),
        Index("idx_message_delivery_status", "is_delivered", "is_read"),
        {"extend_existing": True},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(36), ForeignKey("conversations.id"), nullable=False, index=True
    )
    sender_id = Column(String(36), ForeignKey("users.id"), index=True)

    # Content
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.CHAT, nullable=False)

    # External message details
    external_message_id = Column(String(255))
    from_number = Column(String(20))
    to_number = Column(String(20))

    # Status tracking
    is_delivered = Column(Boolean, default=False, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    delivery_status = Column(String(50))

    # Metadata
    is_edited = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<Message(id='{self.id}', conversation_id='{self.conversation_id}', type={self.message_type.value})>"


# Pydantic Models for API
class ConversationCreate(BaseModel):
    title: Optional[str] = None
    is_group: bool = False
    external_number: Optional[str] = None
    participant_ids: list[str] = Field(default_factory=list)


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_muted: Optional[bool] = None
    status: Optional[ConversationStatus] = None


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    is_group: bool
    external_number: Optional[str]
    status: ConversationStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]
    is_archived: bool
    is_muted: bool
    participant_count: int
    unread_count: int = 0

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str
    message_type: MessageType = MessageType.CHAT
    to_number: Optional[str] = None


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_read: Optional[bool] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: Optional[str]
    content: str
    message_type: MessageType
    external_message_id: Optional[str]
    from_number: Optional[str]
    to_number: Optional[str]
    is_delivered: bool
    is_read: bool
    delivery_status: Optional[str]
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    sender_username: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total_count: int
    unread_total: int


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total_count: int
    has_more: bool
    next_cursor: Optional[str] = None


# Search and filter models
class ConversationFilters(BaseModel):
    status: Optional[ConversationStatus] = None
    is_group: Optional[bool] = None
    is_archived: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class MessageFilters(BaseModel):
    message_type: Optional[MessageType] = None
    sender_id: Optional[str] = None
    is_read: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search_query: Optional[str] = None
