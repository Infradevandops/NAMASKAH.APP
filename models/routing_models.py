"""
Routing and conversation intelligence models for the Namaskah platform.

This module defines SQLAlchemy models for routing rules, routing history,
and conversation intelligence features.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Text, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class RoutingRule(Base):
    """
    Model for routing rules that determine message routing logic.

    Attributes:
        id: Primary key
        name: Human-readable name for the rule
        condition: JSON string defining the routing condition
        action: JSON string defining the routing action
        priority: Priority order for rule evaluation (higher = more important)
        is_active: Whether the rule is currently active
        created_at: Timestamp of rule creation
    """
    __tablename__ = "routing_rules"
    __table_args__ = (
        CheckConstraint('priority >= 0', name='check_priority_non_negative'),
        Index('ix_routing_rules_active_priority', 'is_active', 'priority'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    condition = Column(Text, nullable=False)  # JSON string for conditions
    action = Column(Text, nullable=False)  # JSON string for actions
    priority = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<RoutingRule(id={self.id}, name='{self.name}', priority={self.priority}, active={self.is_active})>"


class RoutingHistory(Base):
    """
    Model for tracking routing decisions made for messages.

    Attributes:
        id: Primary key
        message_id: Foreign key to the message
        rule_id: Foreign key to the routing rule (nullable if no rule matched)
        route_taken: The actual route taken
        confidence_score: Confidence score of the routing decision
        created_at: Timestamp of the routing decision
    """
    __tablename__ = "routing_history"
    __table_args__ = (
        Index('ix_routing_history_message_id', 'message_id'),
        Index('ix_routing_history_rule_id', 'rule_id'),
        Index('ix_routing_history_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("routing_rules.id"), nullable=True, index=True)
    route_taken = Column(String(255), nullable=False)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("Message", back_populates="routing_history")
    rule = relationship("RoutingRule", back_populates="routing_history")

    def __repr__(self):
        return f"<RoutingHistory(id={self.id}, message_id={self.message_id}, route='{self.route_taken}')>"


class ConversationIntelligence(Base):
    """
    Model for storing AI-generated intelligence about conversations.

    Attributes:
        id: Primary key
        conversation_id: Foreign key to the conversation
        sentiment_score: Sentiment analysis score (-1 to 1)
        intent: Detected intent of the conversation
        keywords: JSON string of extracted keywords
        summary: AI-generated summary of the conversation
        created_at: Timestamp of intelligence generation
    """
    __tablename__ = "conversation_intelligence"
    __table_args__ = (
        CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1', name='check_sentiment_range'),
        Index('ix_conversation_intelligence_conversation_id', 'conversation_id'),
        Index('ix_conversation_intelligence_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    sentiment_score = Column(Float, nullable=True)
    intent = Column(String(100), nullable=True)
    keywords = Column(Text, nullable=True)  # JSON string
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="intelligence")

    def __repr__(self):
        return f"<ConversationIntelligence(id={self.id}, conversation_id={self.conversation_id}, intent='{self.intent}')>"
