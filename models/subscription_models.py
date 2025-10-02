#!/usr/bin/env python3
"""
Subscription Models for Namaskah Communication Platform

Enhanced models for subscription management, billing, and usage tracking.
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy import (JSON, Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKey,
                        Index, Integer, Numeric, String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


# Enums
class SubscriptionPlan(str, enum.Enum):
    """Enumeration of available subscription plans"""
    FREE = "free"
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Enumeration of subscription statuses"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING = "pending"


class BillingCycle(str, enum.Enum):
    """Enumeration of billing cycle options"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PaymentStatus(str, enum.Enum):
    """Enumeration of payment statuses"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class UsageType(str, enum.Enum):
    """Enumeration of usage types for billing"""
    SMS_SENT = "sms_sent"
    SMS_RECEIVED = "sms_received"
    VOICE_MINUTES = "voice_minutes"
    VERIFICATION_REQUEST = "verification_request"
    PHONE_NUMBER_RENTAL = "phone_number_rental"
    API_CALL = "api_call"


# SQLAlchemy Models
class SubscriptionPlanConfig(Base):
    """
    Configuration for subscription plans.

    Defines pricing, limits, features, and metadata for subscription plans.
    """

    __tablename__ = "subscription_plan_configs"
    __table_args__ = (
        Index("idx_plan_name", "plan_name"),
        Index("idx_plan_active", "is_active"),
        Index("idx_plan_sort", "sort_order"),
        {"extend_existing": True},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_name = Column(Enum(SubscriptionPlan), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)

    # Pricing
    monthly_price = Column(Numeric(10, 2), nullable=False)
    quarterly_price = Column(Numeric(10, 2))
    yearly_price = Column(Numeric(10, 2))

    # Limits and features
    monthly_sms_limit = Column(Integer, default=0, nullable=False)  # 0 = unlimited
    monthly_voice_minutes_limit = Column(Integer, default=0, nullable=False)
    monthly_verification_limit = Column(Integer, default=0, nullable=False)
    max_phone_numbers = Column(Integer, default=1, nullable=False)
    api_rate_limit = Column(Integer, default=1000, nullable=False)  # Requests per hour

    # Features
    features = Column(JSON)  # List of included features
    smart_routing_enabled = Column(Boolean, default=False, nullable=False)
    ai_assistant_enabled = Column(Boolean, default=False, nullable=False)
    priority_support = Column(Boolean, default=False, nullable=False)
    analytics_enabled = Column(Boolean, default=False, nullable=False)

    # Overage pricing
    sms_overage_rate = Column(Numeric(10, 4), default=0.01, nullable=False)
    voice_overage_rate = Column(Numeric(10, 4), default=0.02, nullable=False)
    verification_overage_rate = Column(Numeric(10, 4), default=0.05, nullable=False)

    # Plan metadata
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subscriptions = relationship("UserSubscription", back_populates="plan_config")


class UserSubscription(Base):
    """User subscription records"""

    __tablename__ = "user_subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    plan_id = Column(String, ForeignKey("subscription_plan_configs.id"), nullable=False)

    # Subscription details
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING)
    billing_cycle = Column(Enum(BillingCycle), default=BillingCycle.MONTHLY)

    # Pricing (locked at subscription time)
    monthly_price = Column(Numeric(10, 2), nullable=False)
    current_price = Column(Numeric(10, 2), nullable=False)

    # Billing dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    next_billing_date = Column(DateTime, nullable=False)
    trial_end_date = Column(DateTime)

    # Cancellation
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    cancel_at_period_end = Column(Boolean, default=False)

    # Payment integration
    stripe_subscription_id = Column(String(200))
    stripe_customer_id = Column(String(200))

    # Usage limits (copied from plan at subscription time)
    monthly_sms_limit = Column(Integer, default=0)
    monthly_voice_minutes_limit = Column(Integer, default=0)
    monthly_verification_limit = Column(Integer, default=0)
    max_phone_numbers = Column(Integer, default=1)

    # Current usage (reset monthly)
    current_sms_usage = Column(Integer, default=0)
    current_voice_usage = Column(Integer, default=0)
    current_verification_usage = Column(Integer, default=0)
    current_phone_numbers = Column(Integer, default=0)

    # Usage reset tracking
    last_usage_reset = Column(DateTime, default=datetime.utcnow)

    # Metadata
    subscription_metadata = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan_config = relationship("SubscriptionPlanConfig", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    usage_records = relationship("UsageRecord", back_populates="subscription")

    # Indexes
    __table_args__ = (
        Index("idx_subscription_user", "user_id"),
        Index("idx_subscription_status", "status"),
        Index("idx_subscription_billing_date", "next_billing_date"),
        Index("idx_subscription_stripe", "stripe_subscription_id"),
        {"extend_existing": True},
    )


class Payment(Base):
    """Payment records for subscriptions and usage"""

    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(String, ForeignKey("user_subscriptions.id"))

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # Payment method
    payment_method = Column(String(50))  # stripe, paypal, etc.
    payment_method_id = Column(String(200))

    # External payment IDs
    stripe_payment_intent_id = Column(String(200))
    stripe_charge_id = Column(String(200))

    # Payment metadata
    description = Column(Text)
    invoice_number = Column(String(100))

    # Billing period (for subscription payments)
    billing_period_start = Column(DateTime)
    billing_period_end = Column(DateTime)

    # Failure information
    failure_code = Column(String(100))
    failure_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime)

    # Relationships
    user = relationship("User")
    subscription = relationship("UserSubscription", back_populates="payments")

    # Indexes
    __table_args__ = (
        Index("idx_payment_user", "user_id"),
        Index("idx_payment_subscription", "subscription_id"),
        Index("idx_payment_status", "status"),
        Index("idx_payment_stripe_intent", "stripe_payment_intent_id"),
        Index("idx_payment_created", "created_at"),
        {"extend_existing": True},
    )


class UsageRecord(Base):
    """Detailed usage tracking for billing and analytics"""

    __tablename__ = "usage_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(String, ForeignKey("user_subscriptions.id"))

    # Usage details
    usage_type = Column(Enum(UsageType), nullable=False)
    quantity = Column(Integer, default=1)
    unit_cost = Column(Numeric(10, 4))
    total_cost = Column(Numeric(10, 4))

    # Resource details
    resource_id = Column(String(200))  # Phone number ID, verification ID, etc.
    resource_metadata = Column(JSON)

    # Billing information
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    is_overage = Column(Boolean, default=False)

    # Timestamps
    usage_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    subscription = relationship("UserSubscription", back_populates="usage_records")

    # Indexes
    __table_args__ = (
        Index("idx_usage_user_period", "user_id", "billing_period_start"),
        Index(
            "idx_usage_subscription_period", "subscription_id", "billing_period_start"
        ),
        Index("idx_usage_type_timestamp", "usage_type", "usage_timestamp"),
        Index("idx_usage_resource", "resource_id"),
        {"extend_existing": True},
    )


class SubscriptionAnalytics(Base):
    """Analytics data for subscription performance"""

    __tablename__ = "subscription_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly

    # Plan analytics
    plan_name = Column(Enum(SubscriptionPlan))

    # Metrics
    new_subscriptions = Column(Integer, default=0)
    cancelled_subscriptions = Column(Integer, default=0)
    active_subscriptions = Column(Integer, default=0)
    total_revenue = Column(Numeric(12, 2), default=0)

    # Usage metrics
    total_sms_usage = Column(Integer, default=0)
    total_voice_usage = Column(Integer, default=0)
    total_verification_usage = Column(Integer, default=0)

    # Performance metrics
    churn_rate = Column(Numeric(5, 4))
    average_revenue_per_user = Column(Numeric(10, 2))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_sub_analytics_date", "date"),
        Index("idx_sub_analytics_plan_date", "plan_name", "date"),
        {"extend_existing": True},
    )


# Pydantic Models for API
class SubscriptionPlanResponse(BaseModel):
    """Response model for subscription plan information"""

    id: str
    plan_name: SubscriptionPlan
    display_name: str
    description: Optional[str]
    monthly_price: Decimal
    quarterly_price: Optional[Decimal]
    yearly_price: Optional[Decimal]
    monthly_sms_limit: int
    monthly_voice_minutes_limit: int
    monthly_verification_limit: int
    max_phone_numbers: int
    features: Optional[List[str]]
    smart_routing_enabled: bool
    ai_assistant_enabled: bool
    priority_support: bool
    analytics_enabled: bool
    sms_overage_rate: Decimal
    voice_overage_rate: Decimal
    verification_overage_rate: Decimal

    class Config:
        from_attributes = True


class SubscriptionCreateRequest(BaseModel):
    """Request model for creating subscription"""

    plan_name: SubscriptionPlan
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    payment_method_id: Optional[str] = None
    trial_days: int = Field(0, ge=0, le=30)

    @validator("plan_name")
    def validate_plan_name(cls, v):
        if v == SubscriptionPlan.FREE:
            raise ValueError("Cannot create paid subscription for free plan")
        return v


class SubscriptionResponse(BaseModel):
    """Response model for subscription details"""

    id: str
    user_id: str
    plan_name: SubscriptionPlan
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    monthly_price: Decimal
    current_price: Decimal
    start_date: datetime
    end_date: datetime
    next_billing_date: datetime
    trial_end_date: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancel_at_period_end: bool

    # Usage information
    monthly_sms_limit: int
    monthly_voice_minutes_limit: int
    monthly_verification_limit: int
    max_phone_numbers: int
    current_sms_usage: int
    current_voice_usage: int
    current_verification_usage: int
    current_phone_numbers: int

    # Usage percentages
    sms_usage_percentage: float = 0.0
    voice_usage_percentage: float = 0.0
    verification_usage_percentage: float = 0.0

    class Config:
        from_attributes = True


class SubscriptionUpdateRequest(BaseModel):
    """Request model for updating subscription"""

    plan_name: Optional[SubscriptionPlan] = None
    billing_cycle: Optional[BillingCycle] = None
    cancel_at_period_end: Optional[bool] = None


class PaymentResponse(BaseModel):
    """Response model for payment information"""

    id: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: Optional[str]
    description: Optional[str]
    invoice_number: Optional[str]
    billing_period_start: Optional[datetime]
    billing_period_end: Optional[datetime]
    created_at: datetime
    paid_at: Optional[datetime]
    failure_message: Optional[str]

    class Config:
        from_attributes = True


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics"""

    user_id: str
    subscription_id: str
    billing_period_start: datetime
    billing_period_end: datetime

    # Current usage
    sms_sent: int
    voice_minutes: int
    verification_requests: int
    phone_numbers_rented: int

    # Costs
    base_subscription_cost: Decimal
    overage_costs: Decimal
    total_cost: Decimal

    # Usage breakdown
    usage_by_type: Dict[str, int]
    costs_by_type: Dict[str, Decimal]


class BillingHistoryResponse(BaseModel):
    """Response model for billing history"""

    payments: List[PaymentResponse]
    total_count: int
    total_amount: Decimal
    period_start: datetime
    period_end: datetime


class SubscriptionAnalyticsResponse(BaseModel):
    """Response model for subscription analytics"""

    date: datetime
    period_type: str
    plan_name: Optional[SubscriptionPlan]
    new_subscriptions: int
    cancelled_subscriptions: int
    active_subscriptions: int
    total_revenue: Decimal
    churn_rate: Optional[Decimal]
    average_revenue_per_user: Optional[Decimal]

    # Usage analytics
    total_sms_usage: int
    total_voice_usage: int
    total_verification_usage: int


class SubscriptionRenewalRequest(BaseModel):
    """Request model for subscription renewal"""

    subscription_id: str
    payment_method_id: Optional[str] = None
    prorate: bool = True


class SubscriptionCancellationRequest(BaseModel):
    """Request model for subscription cancellation"""

    reason: Optional[str] = None
    cancel_immediately: bool = False
    feedback: Optional[str] = None
