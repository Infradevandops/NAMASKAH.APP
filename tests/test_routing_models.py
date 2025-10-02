#!/usr/bin/env python3
"""
Unit tests for routing models
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.routing_models import RoutingRule, RoutingHistory, ConversationIntelligence
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


class TestRoutingRule:
    """Test cases for RoutingRule model"""

    def test_routing_rule_creation(self, db_session):
        """Test creating a routing rule with valid data"""
        rule = RoutingRule(
            name="Test Rule",
            condition='{"type": "keyword", "value": "urgent"}',
            action='{"type": "route", "destination": "priority"}',
            priority=5
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.id is not None
        assert rule.name == "Test Rule"
        assert rule.priority == 5
        assert rule.is_active is True
        assert isinstance(rule.created_at, datetime)

    def test_routing_rule_defaults(self, db_session):
        """Test default values for routing rule"""
        rule = RoutingRule(
            name="Default Rule",
            condition='{"type": "default"}',
            action='{"type": "route", "destination": "standard"}'
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.priority == 0
        assert rule.is_active is True

    def test_routing_rule_repr(self, db_session):
        """Test string representation of routing rule"""
        rule = RoutingRule(
            name="Test Rule",
            condition='{"test": true}',
            action='{"action": "test"}'
        )
        expected = f"<RoutingRule(id=None, name='Test Rule', priority=0, active=True)>"
        assert repr(rule) == expected

    def test_routing_rule_priority_constraint(self, db_session):
        """Test that negative priority raises constraint error"""
        rule = RoutingRule(
            name="Invalid Rule",
            condition='{"test": true}',
            action='{"action": "test"}',
            priority=-1
        )
        db_session.add(rule)

        with pytest.raises(Exception):  # Constraint violation
            db_session.commit()

    @pytest.mark.parametrize("name,condition,action", [
        ("", '{"test": true}', '{"action": "test"}'),
        ("Valid Name", "", '{"action": "test"}'),
        ("Valid Name", '{"test": true}', ""),
    ])
    def test_routing_rule_required_fields(self, db_session, name, condition, action):
        """Test that required fields cannot be null"""
        rule = RoutingRule(
            name=name,
            condition=condition,
            action=action
        )
        db_session.add(rule)

        with pytest.raises(Exception):  # NOT NULL constraint
            db_session.commit()


class TestRoutingHistory:
    """Test cases for RoutingHistory model"""

    def test_routing_history_creation(self, db_session):
        """Test creating routing history with valid data"""
        # First create a rule
        rule = RoutingRule(
            name="History Test Rule",
            condition='{"test": true}',
            action='{"action": "test"}'
        )
        db_session.add(rule)
        db_session.commit()

        history = RoutingHistory(
            message_id=1,
            rule_id=rule.id,
            route_taken="test_route",
            confidence_score=0.95
        )
        db_session.add(history)
        db_session.commit()

        assert history.id is not None
        assert history.message_id == 1
        assert history.rule_id == rule.id
        assert history.route_taken == "test_route"
        assert history.confidence_score == 0.95

    def test_routing_history_without_rule(self, db_session):
        """Test creating routing history without a matching rule"""
        history = RoutingHistory(
            message_id=2,
            route_taken="default_route"
        )
        db_session.add(history)
        db_session.commit()

        assert history.rule_id is None
        assert history.confidence_score is None

    def test_routing_history_repr(self, db_session):
        """Test string representation of routing history"""
        history = RoutingHistory(
            message_id=1,
            route_taken="test_route"
        )
        expected = "<RoutingHistory(id=None, message_id=1, route='test_route')>"
        assert repr(history) == expected

    def test_routing_history_required_fields(self, db_session):
        """Test that required fields cannot be null"""
        history = RoutingHistory(
            message_id=1,
            route_taken=""  # Empty string should fail
        )
        db_session.add(history)

        with pytest.raises(Exception):  # NOT NULL constraint
            db_session.commit()


class TestConversationIntelligence:
    """Test cases for ConversationIntelligence model"""

    def test_conversation_intelligence_creation(self, db_session):
        """Test creating conversation intelligence with valid data"""
        intelligence = ConversationIntelligence(
            conversation_id=1,
            sentiment_score=0.8,
            intent="question",
            keywords='["help", "support"]',
            summary="User asking for help with billing"
        )
        db_session.add(intelligence)
        db_session.commit()

        assert intelligence.id is not None
        assert intelligence.conversation_id == 1
        assert intelligence.sentiment_score == 0.8
        assert intelligence.intent == "question"
        assert intelligence.keywords == '["help", "support"]'
        assert intelligence.summary == "User asking for help with billing"

    def test_conversation_intelligence_minimal(self, db_session):
        """Test creating conversation intelligence with minimal data"""
        intelligence = ConversationIntelligence(
            conversation_id=2
        )
        db_session.add(intelligence)
        db_session.commit()

        assert intelligence.sentiment_score is None
        assert intelligence.intent is None
        assert intelligence.keywords is None
        assert intelligence.summary is None

    def test_conversation_intelligence_repr(self, db_session):
        """Test string representation of conversation intelligence"""
        intelligence = ConversationIntelligence(
            conversation_id=1,
            intent="greeting"
        )
        expected = "<ConversationIntelligence(id=None, conversation_id=1, intent='greeting')>"
        assert repr(intelligence) == expected

    @pytest.mark.parametrize("sentiment_score", [-1.5, 1.5, 2.0])
    def test_conversation_intelligence_sentiment_constraint(self, db_session, sentiment_score):
        """Test that sentiment score must be between -1 and 1"""
        intelligence = ConversationIntelligence(
            conversation_id=1,
            sentiment_score=sentiment_score
        )
        db_session.add(intelligence)

        with pytest.raises(Exception):  # Constraint violation
            db_session.commit()

    @pytest.mark.parametrize("sentiment_score", [-1.0, 0.0, 1.0, 0.5, -0.3])
    def test_conversation_intelligence_valid_sentiment(self, db_session, sentiment_score):
        """Test that valid sentiment scores are accepted"""
        intelligence = ConversationIntelligence(
            conversation_id=1,
            sentiment_score=sentiment_score
        )
        db_session.add(intelligence)
        db_session.commit()

        assert intelligence.sentiment_score == sentiment_score

    def test_conversation_intelligence_required_fields(self, db_session):
        """Test that conversation_id is required"""
        intelligence = ConversationIntelligence()
        db_session.add(intelligence)

        with pytest.raises(Exception):  # NOT NULL constraint
            db_session.commit()


class TestModelRelationships:
    """Test cases for model relationships"""

    def test_routing_history_rule_relationship(self, db_session):
        """Test relationship between RoutingHistory and RoutingRule"""
        # Create rule
        rule = RoutingRule(
            name="Relationship Test",
            condition='{"test": true}',
            action='{"action": "test"}'
        )
        db_session.add(rule)
        db_session.commit()

        # Create history referencing the rule
        history = RoutingHistory(
            message_id=1,
            rule_id=rule.id,
            route_taken="test_route"
        )
        db_session.add(history)
        db_session.commit()

        # Test relationship loading
        loaded_history = db_session.query(RoutingHistory).filter_by(id=history.id).first()
        assert loaded_history.rule == rule
        assert loaded_history.rule.name == "Relationship Test"

    def test_routing_history_no_rule_relationship(self, db_session):
        """Test RoutingHistory without rule relationship"""
        history = RoutingHistory(
            message_id=2,
            route_taken="no_rule_route"
        )
        db_session.add(history)
        db_session.commit()

        loaded_history = db_session.query(RoutingHistory).filter_by(id=history.id).first()
        assert loaded_history.rule is None


if __name__ == "__main__":
    pytest.main([__file__])
