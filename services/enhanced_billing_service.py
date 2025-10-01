#!/usr/bin/env python3
"""
Enhanced Billing Service for CumApp
Advanced billing features including prorated billing, usage monitoring, and forecasting
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.subscription_models import (
    UserSubscription, SubscriptionPlanConfig, Payment, UsageRecord,
    SubscriptionStatus, PaymentStatus, UsageType, BillingCycle
)
from models.user_models import User
from services.payment_gateway_adapter import PaymentGatewayAdapter
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class BillingEventType(Enum):
    """Types of billing events"""
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_DOWNGRADED = "subscription_downgraded"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    USAGE_THRESHOLD_REACHED = "usage_threshold_reached"
    OVERAGE_INCURRED = "overage_incurred"


@dataclass
class ProratedBillingCalculation:
    """Result of prorated billing calculation"""
    old_plan_credit: Decimal
    new_plan_cost: Decimal
    prorated_amount: Decimal
    effective_date: datetime
    next_billing_date: datetime
    description: str


@dataclass
class UsageAlert:
    """Usage threshold alert"""
    usage_type: UsageType
    current_usage: int
    limit: int
    percentage: float
    threshold: float
    alert_level: str  # 'warning', 'critical', 'exceeded'


@dataclass
class BillingForecast:
    """Billing forecast data"""
    current_period_cost: Decimal
    projected_monthly_cost: Decimal
    projected_overage_cost: Decimal
    usage_trend: Dict[str, float]
    recommendations: List[str]


class EnhancedBillingService:
    """Enhanced billing service with advanced features"""
    
    def __init__(
        self,
        db: Session,
        payment_gateway: PaymentGatewayAdapter,
        notification_service: NotificationService
    ):
        self.db = db
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service
        
        # Usage alert thresholds
        self.usage_thresholds = {
            "warning": 75.0,    # 75%
            "critical": 90.0,   # 90%
            "exceeded": 100.0   # 100%
        }
    
    def calculate_prorated_billing(
        self,
        user_id: str,
        new_plan_id: str,
        effective_date: Optional[datetime] = None
    ) -> ProratedBillingCalculation:
        """
        Calculate prorated billing for plan changes
        
        Args:
            user_id: User ID
            new_plan_id: New subscription plan ID
            effective_date: When the change should take effect
            
        Returns:
            ProratedBillingCalculation with detailed breakdown
        """
        if effective_date is None:
            effective_date = datetime.utcnow()
        
        # Get current subscription
        current_subscription = self.db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()
        
        if not current_subscription:
            raise ValueError("No active subscription found for user")
        
        # Get new plan configuration
        new_plan = self.db.query(SubscriptionPlanConfig).filter(
            SubscriptionPlanConfig.id == new_plan_id
        ).first()
        
        if not new_plan:
            raise ValueError("New plan not found")
        
        # Calculate billing period details
        current_period_start = current_subscription.start_date
        current_period_end = current_subscription.end_date
        total_days = (current_period_end - current_period_start).days
        remaining_days = (current_period_end - effective_date).days
        
        if remaining_days < 0:
            remaining_days = 0
        
        # Calculate daily rates
        current_daily_rate = current_subscription.current_price / Decimal(total_days)
        
        # Determine new plan price based on billing cycle
        if current_subscription.billing_cycle == BillingCycle.MONTHLY:
            new_plan_price = new_plan.monthly_price
        elif current_subscription.billing_cycle == BillingCycle.QUARTERLY:
            new_plan_price = new_plan.quarterly_price or (new_plan.monthly_price * 3)
        else:  # YEARLY
            new_plan_price = new_plan.yearly_price or (new_plan.monthly_price * 12)
        
        new_daily_rate = new_plan_price / Decimal(total_days)
        
        # Calculate prorated amounts
        old_plan_credit = current_daily_rate * Decimal(remaining_days)
        new_plan_cost = new_daily_rate * Decimal(remaining_days)
        prorated_amount = new_plan_cost - old_plan_credit
        
        # Round to 2 decimal places
        prorated_amount = prorated_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        old_plan_credit = old_plan_credit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        new_plan_cost = new_plan_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Generate description
        if prorated_amount > 0:
            description = f"Upgrade to {new_plan.display_name} - prorated charge for remaining {remaining_days} days"
        elif prorated_amount < 0:
            description = f"Downgrade to {new_plan.display_name} - prorated credit for remaining {remaining_days} days"
        else:
            description = f"Plan change to {new_plan.display_name} - no additional charge"
        
        return ProratedBillingCalculation(
            old_plan_credit=old_plan_credit,
            new_plan_cost=new_plan_cost,
            prorated_amount=prorated_amount,
            effective_date=effective_date,
            next_billing_date=current_period_end,
            description=description
        )
    
    def change_subscription_plan(
        self,
        user_id: str,
        new_plan_id: str,
        payment_method_id: Optional[str] = None,
        effective_immediately: bool = True
    ) -> Dict[str, Any]:
        """
        Change user's subscription plan with prorated billing
        
        Args:
            user_id: User ID
            new_plan_id: New plan ID
            payment_method_id: Payment method for charges
            effective_immediately: Whether to apply change immediately
            
        Returns:
            Dictionary with change result and payment details
        """
        try:
            # Calculate prorated billing
            calculation = self.calculate_prorated_billing(user_id, new_plan_id)
            
            # Get current subscription
            current_subscription = self.db.query(UserSubscription).filter(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == SubscriptionStatus.ACTIVE
                )
            ).first()
            
            # Get new plan
            new_plan = self.db.query(SubscriptionPlanConfig).filter(
                SubscriptionPlanConfig.id == new_plan_id
            ).first()
            
            result = {
                "success": False,
                "calculation": calculation,
                "payment": None,
                "subscription_updated": False
            }
            
            # Handle payment if required
            if calculation.prorated_amount > 0:
                # Charge required
                payment_result = self.payment_gateway.create_charge(
                    amount=int(calculation.prorated_amount * 100),  # Convert to cents
                    currency="USD",
                    source=payment_method_id,
                    description=calculation.description
                )
                
                if "error" in payment_result:
                    result["error"] = payment_result["error"]
                    return result
                
                # Record payment
                payment = Payment(
                    user_id=user_id,
                    subscription_id=current_subscription.id,
                    amount=calculation.prorated_amount,
                    currency="USD",
                    status=PaymentStatus.COMPLETED,
                    payment_method="stripe",  # TODO: Make dynamic
                    description=calculation.description,
                    billing_period_start=calculation.effective_date,
                    billing_period_end=calculation.next_billing_date,
                    paid_at=datetime.utcnow()
                )
                self.db.add(payment)
                result["payment"] = payment_result
            
            elif calculation.prorated_amount < 0:
                # Credit to be applied - record as negative payment
                payment = Payment(
                    user_id=user_id,
                    subscription_id=current_subscription.id,
                    amount=calculation.prorated_amount,
                    currency="USD",
                    status=PaymentStatus.COMPLETED,
                    payment_method="credit",
                    description=f"Credit for plan change: {calculation.description}",
                    billing_period_start=calculation.effective_date,
                    billing_period_end=calculation.next_billing_date,
                    paid_at=datetime.utcnow()
                )
                self.db.add(payment)
            
            # Update subscription
            if effective_immediately:
                current_subscription.plan_id = new_plan_id
                current_subscription.current_price = (
                    new_plan.monthly_price if current_subscription.billing_cycle == BillingCycle.MONTHLY
                    else new_plan.quarterly_price or (new_plan.monthly_price * 3)
                    if current_subscription.billing_cycle == BillingCycle.QUARTERLY
                    else new_plan.yearly_price or (new_plan.monthly_price * 12)
                )
                
                # Update limits
                current_subscription.monthly_sms_limit = new_plan.monthly_sms_limit
                current_subscription.monthly_voice_minutes_limit = new_plan.monthly_voice_minutes_limit
                current_subscription.monthly_verification_limit = new_plan.monthly_verification_limit
                current_subscription.max_phone_numbers = new_plan.max_phone_numbers
                
                current_subscription.updated_at = datetime.utcnow()
                result["subscription_updated"] = True
            
            self.db.commit()
            
            # Send notification
            event_type = (
                BillingEventType.SUBSCRIPTION_UPGRADED 
                if calculation.prorated_amount > 0 
                else BillingEventType.SUBSCRIPTION_DOWNGRADED
            )
            
            await self.notification_service.send_billing_notification(
                user_id=user_id,
                event_type=event_type,
                details={
                    "old_plan": current_subscription.plan_config.display_name,
                    "new_plan": new_plan.display_name,
                    "prorated_amount": float(calculation.prorated_amount),
                    "effective_date": calculation.effective_date.isoformat()
                }
            )
            
            result["success"] = True
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Subscription plan change failed: {e}")
            return {"success": False, "error": str(e)}
    
    def track_usage(
        self,
        user_id: str,
        usage_type: UsageType,
        quantity: int = 1,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track usage and check for threshold alerts
        
        Args:
            user_id: User ID
            usage_type: Type of usage
            quantity: Usage quantity
            resource_id: Associated resource ID
            metadata: Additional metadata
            
        Returns:
            Usage tracking result with alerts
        """
        try:
            # Get current subscription
            subscription = self.db.query(UserSubscription).filter(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == SubscriptionStatus.ACTIVE
                )
            ).first()
            
            if not subscription:
                return {"success": False, "error": "No active subscription"}
            
            # Calculate billing period
            now = datetime.utcnow()
            billing_period_start = subscription.last_usage_reset
            billing_period_end = subscription.next_billing_date
            
            # Create usage record
            usage_record = UsageRecord(
                user_id=user_id,
                subscription_id=subscription.id,
                usage_type=usage_type,
                quantity=quantity,
                resource_id=resource_id,
                resource_metadata=metadata,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end,
                usage_timestamp=now
            )
            
            # Calculate cost if overage
            plan_config = subscription.plan_config
            is_overage = False
            unit_cost = Decimal('0')
            
            # Update current usage counters
            if usage_type == UsageType.SMS_SENT:
                subscription.current_sms_usage += quantity
                if subscription.current_sms_usage > subscription.monthly_sms_limit:
                    is_overage = True
                    unit_cost = plan_config.sms_overage_rate
            elif usage_type == UsageType.VOICE_MINUTES:
                subscription.current_voice_usage += quantity
                if subscription.current_voice_usage > subscription.monthly_voice_minutes_limit:
                    is_overage = True
                    unit_cost = plan_config.voice_overage_rate
            elif usage_type == UsageType.VERIFICATION_REQUEST:
                subscription.current_verification_usage += quantity
                if subscription.current_verification_usage > subscription.monthly_verification_limit:
                    is_overage = True
                    unit_cost = plan_config.verification_overage_rate
            
            # Set usage record cost
            if is_overage:
                usage_record.is_overage = True
                usage_record.unit_cost = unit_cost
                usage_record.total_cost = unit_cost * Decimal(quantity)
            
            self.db.add(usage_record)
            subscription.updated_at = now
            self.db.commit()
            
            # Check for usage alerts
            alerts = self.check_usage_alerts(user_id)
            
            # Send notifications for new alerts
            for alert in alerts:
                if alert.alert_level in ['critical', 'exceeded']:
                    await self.notification_service.send_usage_alert(
                        user_id=user_id,
                        alert=alert
                    )
            
            return {
                "success": True,
                "usage_recorded": True,
                "is_overage": is_overage,
                "overage_cost": float(usage_record.total_cost) if usage_record.total_cost else 0,
                "alerts": [
                    {
                        "type": alert.usage_type.value,
                        "percentage": alert.percentage,
                        "level": alert.alert_level
                    }
                    for alert in alerts
                ]
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Usage tracking failed: {e}")
            return {"success": False, "error": str(e)}
    
    def check_usage_alerts(self, user_id: str) -> List[UsageAlert]:
        """
        Check current usage against thresholds and return alerts
        
        Args:
            user_id: User ID
            
        Returns:
            List of usage alerts
        """
        alerts = []
        
        # Get current subscription
        subscription = self.db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()
        
        if not subscription:
            return alerts
        
        # Check SMS usage
        if subscription.monthly_sms_limit > 0:
            sms_percentage = (subscription.current_sms_usage / subscription.monthly_sms_limit) * 100
            alert_level = self._get_alert_level(sms_percentage)
            
            if alert_level:
                alerts.append(UsageAlert(
                    usage_type=UsageType.SMS_SENT,
                    current_usage=subscription.current_sms_usage,
                    limit=subscription.monthly_sms_limit,
                    percentage=sms_percentage,
                    threshold=self.usage_thresholds[alert_level],
                    alert_level=alert_level
                ))
        
        # Check voice usage
        if subscription.monthly_voice_minutes_limit > 0:
            voice_percentage = (subscription.current_voice_usage / subscription.monthly_voice_minutes_limit) * 100
            alert_level = self._get_alert_level(voice_percentage)
            
            if alert_level:
                alerts.append(UsageAlert(
                    usage_type=UsageType.VOICE_MINUTES,
                    current_usage=subscription.current_voice_usage,
                    limit=subscription.monthly_voice_minutes_limit,
                    percentage=voice_percentage,
                    threshold=self.usage_thresholds[alert_level],
                    alert_level=alert_level
                ))
        
        # Check verification usage
        if subscription.monthly_verification_limit > 0:
            verification_percentage = (subscription.current_verification_usage / subscription.monthly_verification_limit) * 100
            alert_level = self._get_alert_level(verification_percentage)
            
            if alert_level:
                alerts.append(UsageAlert(
                    usage_type=UsageType.VERIFICATION_REQUEST,
                    current_usage=subscription.current_verification_usage,
                    limit=subscription.monthly_verification_limit,
                    percentage=verification_percentage,
                    threshold=self.usage_thresholds[alert_level],
                    alert_level=alert_level
                ))
        
        return alerts
    
    def _get_alert_level(self, percentage: float) -> Optional[str]:
        """Get alert level based on usage percentage"""
        if percentage >= self.usage_thresholds["exceeded"]:
            return "exceeded"
        elif percentage >= self.usage_thresholds["critical"]:
            return "critical"
        elif percentage >= self.usage_thresholds["warning"]:
            return "warning"
        return None
    
    def generate_billing_forecast(
        self,
        user_id: str,
        forecast_days: int = 30
    ) -> BillingForecast:
        """
        Generate billing forecast based on usage patterns
        
        Args:
            user_id: User ID
            forecast_days: Number of days to forecast
            
        Returns:
            BillingForecast with projections and recommendations
        """
        # Get current subscription
        subscription = self.db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()
        
        if not subscription:
            raise ValueError("No active subscription found")
        
        # Get usage history for trend analysis
        usage_history = self.db.query(UsageRecord).filter(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.usage_timestamp >= datetime.utcnow() - timedelta(days=90)
            )
        ).order_by(desc(UsageRecord.usage_timestamp)).all()
        
        # Calculate current period cost
        current_period_cost = subscription.current_price
        
        # Calculate usage trends
        usage_trends = self._calculate_usage_trends(usage_history, forecast_days)
        
        # Project overage costs
        projected_overage_cost = self._calculate_projected_overage(
            subscription, usage_trends, forecast_days
        )
        
        # Calculate total projected cost
        projected_monthly_cost = current_period_cost + projected_overage_cost
        
        # Generate recommendations
        recommendations = self._generate_billing_recommendations(
            subscription, usage_trends, projected_overage_cost
        )
        
        return BillingForecast(
            current_period_cost=current_period_cost,
            projected_monthly_cost=projected_monthly_cost,
            projected_overage_cost=projected_overage_cost,
            usage_trend=usage_trends,
            recommendations=recommendations
        )
    
    def _calculate_usage_trends(
        self,
        usage_history: List[UsageRecord],
        forecast_days: int
    ) -> Dict[str, float]:
        """Calculate usage trends from historical data"""
        trends = {}
        
        # Group usage by type and calculate daily averages
        usage_by_type = {}
        for record in usage_history:
            usage_type = record.usage_type.value
            if usage_type not in usage_by_type:
                usage_by_type[usage_type] = []
            usage_by_type[usage_type].append(record.quantity)
        
        # Calculate trends
        for usage_type, quantities in usage_by_type.items():
            if quantities:
                daily_average = sum(quantities) / len(quantities)
                projected_monthly = daily_average * forecast_days
                trends[usage_type] = projected_monthly
            else:
                trends[usage_type] = 0
        
        return trends
    
    def _calculate_projected_overage(
        self,
        subscription: UserSubscription,
        usage_trends: Dict[str, float],
        forecast_days: int
    ) -> Decimal:
        """Calculate projected overage costs"""
        total_overage_cost = Decimal('0')
        plan_config = subscription.plan_config
        
        # SMS overage
        projected_sms = usage_trends.get('sms_sent', 0)
        if projected_sms > subscription.monthly_sms_limit:
            sms_overage = projected_sms - subscription.monthly_sms_limit
            total_overage_cost += Decimal(str(sms_overage)) * plan_config.sms_overage_rate
        
        # Voice overage
        projected_voice = usage_trends.get('voice_minutes', 0)
        if projected_voice > subscription.monthly_voice_minutes_limit:
            voice_overage = projected_voice - subscription.monthly_voice_minutes_limit
            total_overage_cost += Decimal(str(voice_overage)) * plan_config.voice_overage_rate
        
        # Verification overage
        projected_verification = usage_trends.get('verification_request', 0)
        if projected_verification > subscription.monthly_verification_limit:
            verification_overage = projected_verification - subscription.monthly_verification_limit
            total_overage_cost += Decimal(str(verification_overage)) * plan_config.verification_overage_rate
        
        return total_overage_cost
    
    def _generate_billing_recommendations(
        self,
        subscription: UserSubscription,
        usage_trends: Dict[str, float],
        projected_overage_cost: Decimal
    ) -> List[str]:
        """Generate billing optimization recommendations"""
        recommendations = []
        
        # Check if upgrade would be cost-effective
        if projected_overage_cost > Decimal('10'):  # $10 threshold
            recommendations.append(
                f"Consider upgrading your plan to avoid ${projected_overage_cost:.2f} in overage charges"
            )
        
        # Check for underutilization
        sms_utilization = (subscription.current_sms_usage / subscription.monthly_sms_limit) * 100 if subscription.monthly_sms_limit > 0 else 0
        voice_utilization = (subscription.current_voice_usage / subscription.monthly_voice_minutes_limit) * 100 if subscription.monthly_voice_minutes_limit > 0 else 0
        
        if sms_utilization < 25 and voice_utilization < 25:
            recommendations.append(
                "You're using less than 25% of your plan limits. Consider downgrading to save money."
            )
        
        # Usage optimization tips
        if usage_trends.get('sms_sent', 0) > subscription.monthly_sms_limit * 0.8:
            recommendations.append(
                "Consider using bulk messaging features to reduce SMS costs"
            )
        
        return recommendations
    
    def get_billing_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive billing summary for user
        
        Args:
            user_id: User ID
            
        Returns:
            Complete billing summary
        """
        # Get current subscription
        subscription = self.db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()
        
        if not subscription:
            return {"error": "No active subscription found"}
        
        # Get usage alerts
        alerts = self.check_usage_alerts(user_id)
        
        # Get billing forecast
        forecast = self.generate_billing_forecast(user_id)
        
        # Get recent payments
        recent_payments = self.db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(desc(Payment.created_at)).limit(5).all()
        
        return {
            "subscription": {
                "plan_name": subscription.plan_config.display_name,
                "status": subscription.status.value,
                "current_price": float(subscription.current_price),
                "billing_cycle": subscription.billing_cycle.value,
                "next_billing_date": subscription.next_billing_date.isoformat(),
            },
            "usage": {
                "sms": {
                    "used": subscription.current_sms_usage,
                    "limit": subscription.monthly_sms_limit,
                    "percentage": (subscription.current_sms_usage / subscription.monthly_sms_limit * 100) if subscription.monthly_sms_limit > 0 else 0
                },
                "voice": {
                    "used": subscription.current_voice_usage,
                    "limit": subscription.monthly_voice_minutes_limit,
                    "percentage": (subscription.current_voice_usage / subscription.monthly_voice_minutes_limit * 100) if subscription.monthly_voice_minutes_limit > 0 else 0
                },
                "verification": {
                    "used": subscription.current_verification_usage,
                    "limit": subscription.monthly_verification_limit,
                    "percentage": (subscription.current_verification_usage / subscription.monthly_verification_limit * 100) if subscription.monthly_verification_limit > 0 else 0
                }
            },
            "alerts": [
                {
                    "type": alert.usage_type.value,
                    "level": alert.alert_level,
                    "percentage": alert.percentage,
                    "message": f"{alert.usage_type.value} usage at {alert.percentage:.1f}%"
                }
                for alert in alerts
            ],
            "forecast": {
                "current_period_cost": float(forecast.current_period_cost),
                "projected_monthly_cost": float(forecast.projected_monthly_cost),
                "projected_overage_cost": float(forecast.projected_overage_cost),
                "recommendations": forecast.recommendations
            },
            "recent_payments": [
                {
                    "id": payment.id,
                    "amount": float(payment.amount),
                    "status": payment.status.value,
                    "description": payment.description,
                    "created_at": payment.created_at.isoformat()
                }
                for payment in recent_payments
            ]
        }