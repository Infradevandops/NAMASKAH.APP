#!/usr/bin/env python3
"""
Unit tests for phone number models
"""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.phone_number_models import (
    PhoneNumber,
    PhoneNumberUsage,
    PhoneNumberStatus,
    PhoneNumberProvider,
    PhoneNumberCapability,
)
from models.user_models import User
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


class TestPhoneNumberModel:
    """Test cases for PhoneNumber model"""

    def test_phone_number_creation(self, db_session):
        """Test creating a phone number with valid data"""
        phone = PhoneNumber(
            phone_number="+1234567890",
            provider=PhoneNumberProvider.TWILIO,
            provider_id="PN1234567890",
            country_code="US",
            area_code="234",
            region="California",
            monthly_cost=Decimal("9.99"),
            sms_cost_per_message=Decimal("0.0075"),
            setup_fee=Decimal("1.00")
        )
        db_session.add(phone)
        db_session.commit()

        assert phone.id is not None
        assert phone.phone_number == "+1234567890"
        assert phone.provider == PhoneNumberProvider.TWILIO
        assert phone.status == PhoneNumberStatus.AVAILABLE
        assert phone.monthly_cost == Decimal("9.99")
        assert phone.total_sms_sent == 0
        assert isinstance(phone.created_at, datetime)

    def test_phone_number_with_owner(self, db_session):
        """Test phone number with owner relationship"""
        user = User(
            email="owner@example.com",
            username="owner",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        phone = PhoneNumber(
            phone_number="+1987654321",
            provider=PhoneNumberProvider.TWILIO,
            country_code="US",
            status=PhoneNumberStatus.ACTIVE,
            owner_id=user.id
        )
        db_session.add(phone)
        db_session.commit()

        assert phone.owner_id == user.id
        assert phone.status == PhoneNumberStatus.ACTIVE

    def test_phone_number_repr(self, db_session):
        """Test string representation of phone number"""
        phone = PhoneNumber(
            phone_number="+1555123456",
            provider=PhoneNumberProvider.MOCK,
            country_code="US",
            status=PhoneNumberStatus.PURCHASED
        )
        expected = f"<PhoneNumber(id='{phone.id}', number='+1555123456', status={phone.status.value}, provider={phone.provider.value})>"
        assert repr(phone) == expected

    def test_phone_number_unique_constraint(self, db_session):
        """Test unique constraint on phone_number"""
        phone1 = PhoneNumber(
            phone_number="+1444987654",
            provider=PhoneNumberProvider.TWILIO,
            country_code="US"
        )
        db_session.add(phone1)
        db_session.commit()

        phone2 = PhoneNumber(
            phone_number="+1444987654",  # Same number
            provider=PhoneNumberProvider.TEXTVERIFIED,
            country_code="US"
        )
        db_session.add(phone2)

        with pytest.raises(Exception):  # Unique constraint violation
            db_session.commit()

    @pytest.mark.parametrize("total_sms_sent", [-1, -10])
    def test_phone_number_usage_constraints(self, db_session, total_sms_sent):
        """Test that usage counters cannot be negative"""
        phone = PhoneNumber(
            phone_number="+1999888777",
            provider=PhoneNumberProvider.MOCK,
            country_code="US",
            total_sms_sent=total_sms_sent
        )
        db_session.add(phone)

        with pytest.raises(Exception):  # Check constraint violation
            db_session.commit()

    def test_phone_number_valid_usage(self, db_session):
        """Test that valid usage values are accepted"""
        phone = PhoneNumber(
            phone_number="+1888777666",
            provider=PhoneNumberProvider.MOCK,
            country_code="US",
            total_sms_sent=100,
            total_voice_minutes=50
        )
        db_session.add(phone)
        db_session.commit()

        assert phone.total_sms_sent == 100
        assert phone.total_voice_minutes == 50


class TestPhoneNumberUsageModel:
    """Test cases for PhoneNumberUsage model"""

    def test_phone_number_usage_creation(self, db_session):
        """Test creating phone number usage with valid data"""
        user = User(
            email="usage@example.com",
            username="usageuser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        phone = PhoneNumber(
            phone_number="+1777555333",
            provider=PhoneNumberProvider.MOCK,
            country_code="US"
        )
        db_session.add(phone)
        db_session.commit()

        usage_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        usage = PhoneNumberUsage(
            phone_number_id=phone.id,
            user_id=user.id,
            usage_date=usage_date,
            sms_sent=10,
            sms_received=5,
            voice_minutes=30,
            sms_cost=Decimal("0.075"),
            voice_cost=Decimal("0.30"),
            total_cost=Decimal("0.375")
        )
        db_session.add(usage)
        db_session.commit()

        assert usage.id is not None
        assert usage.phone_number_id == phone.id
        assert usage.user_id == user.id
        assert usage.sms_sent == 10
        assert usage.total_cost == Decimal("0.375")

    def test_phone_number_usage_relationships(self, db_session):
        """Test relationships in phone number usage"""
        user = User(
            email="rel@example.com",
            username="reluser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        phone = PhoneNumber(
            phone_number="+1666444222",
            provider=PhoneNumberProvider.MOCK,
            country_code="US"
        )
        db_session.add(phone)
        db_session.commit()

        usage = PhoneNumberUsage(
            phone_number_id=phone.id,
            user_id=user.id,
            usage_date=datetime.utcnow(),
            sms_sent=1
        )
        db_session.add(usage)
        db_session.commit()

        # Test relationships
        loaded_usage = db_session.query(PhoneNumberUsage).filter_by(id=usage.id).first()
        assert loaded_usage.phone_number == phone
        assert loaded_usage.user == user

    def test_phone_number_usage_repr(self, db_session):
        """Test string representation of phone number usage"""
        usage = PhoneNumberUsage(
            phone_number_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            usage_date=datetime.utcnow(),
            total_cost=Decimal("1.50")
        )
        expected = f"<PhoneNumberUsage(id='{usage.id}', phone_number_id='{usage.phone_number_id}', date='{usage.usage_date}', total_cost={usage.total_cost})>"
        assert repr(usage) == expected

    @pytest.mark.parametrize("sms_cost", [Decimal("-0.01"), Decimal("-1.00")])
    def test_phone_number_usage_cost_constraints(self, db_session, sms_cost):
        """Test that costs cannot be negative"""
        user = User(
            email="cost@example.com",
            username="costuser",
            hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        phone = PhoneNumber(
            phone_number="+1555666777",
            provider=PhoneNumberProvider.MOCK,
            country_code="US"
        )
        db_session.add(phone)
        db_session.commit()

        usage = PhoneNumberUsage(
            phone_number_id=phone.id,
            user_id=user.id,
            usage_date=datetime.utcnow(),
            sms_cost=sms_cost
        )
        db_session.add(usage)

        with pytest.raises(Exception):  # Check constraint violation
            db_session.commit()


if __name__ == "__main__":
    pytest.main([__file__])
