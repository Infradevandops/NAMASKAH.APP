from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    condition = Column(String, nullable=False)  # JSON string for conditions
    action = Column(String, nullable=False)  # JSON string for actions
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RoutingHistory(Base):
    __tablename__ = "routing_history"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("routing_rules.id"), nullable=True)
    route_taken = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message")
    rule = relationship("RoutingRule")

class ConversationIntelligence(Base):
    __tablename__ = "conversation_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sentiment_score = Column(Float, nullable=True)
    intent = Column(String, nullable=True)
    keywords = Column(String, nullable=True)  # JSON string
    summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation")
