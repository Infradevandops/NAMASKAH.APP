#!/usr/bin/env python3
"""
Enhanced Billing API for namaskah
Comprehensive billing management with advanced features
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from core.database import get_db
from services.enhanced_billing_service import EnhancedBillingService
from services.payment_gateway_factory import payment_gateway_factory, PaymentRegion
from services.notification_service import NotificationService
from models.subscription_models import (
    SubscriptionCreateRequest, SubscriptionResponse, SubscriptionUpdateRequest,
    PaymentResponse, UsageStatsResponse, BillingHistoryResponse,
    SubscriptionPlanResponse
)
from auth.jwt_handler import get_current_user
from models.user_models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])


def get_enhanced_billing_service(
    db: Session = Depends(get_db),
    gateway_type: str = Query("auto", description="Payment gateway preference"),
    region: Optional[str] = Query(None, description="Payment region"),
    country_code: Optional[str] = Query(None, description="Country code for regional optimization")
) -> EnhancedBillingService:
    """Get enhanced billing service with optimal payment gateway"""
    
    # Determine optimal payment gateway
    payment_region = None
    if region:
        try:
            payment_region = PaymentRegion(region.lower())
        except ValueError:
            pass
    
    if gateway_type == "auto":
        gateway = payment_gateway_factory.get_optimal_gateway(
            region=payment_region,
            country_code=country_code
        )
    else:
        # Get specific gateway (fallback to optimal if not available)
        gateway = payment_gateway_factory.gateways.get(gateway_type)
        if not gateway:
            gateway = payment_gateway_factory.get_optimal_gateway(
                region=payment_region,
                country_code=country_code
            )
    
    if not gateway:
        raise HTTPException(
            status_code=503,
            detail="No payment gateway available for your region"
        )
    
    notification_service = NotificationService()
    return EnhancedBillingService(db, gateway, notification_service)


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    db: Session = Depends(get_db),
    active_only: bool = Query(True, description="Return only active plans")
):
    """Get available subscription plans"""
    try:
        from models.subscription_models import SubscriptionPlanConfig
        
        query = db.query(SubscriptionPlanConfig)
        if active_only:
            query = query.filter(SubscriptionPlanConfig.is_active == True)
        
        plans = query.order_by(SubscriptionPlanConfig.sort_order).all()
        return plans
        
    except Exception as e:
        logger.error(f"Failed to get subscription plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription plans")


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription details"""
    try:
        from models.subscription_models import UserSubscription, SubscriptionStatus
        from sqlalchemy import and_
        
        subscription = db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == current_user.id,
                UserSubscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        # Calculate usage percentages
        subscription.sms_usage_percentage = (
            (subscription.current_sms_usage / subscription.monthly_sms_limit * 100)
            if subscription.monthly_sms_limit > 0 else 0
        )
        subscription.voice_usage_percentage = (
            (subscription.current_voice_usage / subscription.monthly_voice_minutes_limit * 100)
            if subscription.monthly_voice_minutes_limit > 0 else 0
        )
        subscription.verification_usage_percentage = (
            (subscription.current_verification_usage / subscription.monthly_verification_limit * 100)
            if subscription.monthly_verification_limit > 0 else 0
        )
        
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription")


@router.post("/subscription/change-plan")
async def change_subscription_plan(
    new_plan_id: str = Body(..., description="New subscription plan ID"),
    payment_method_id: Optional[str] = Body(None, description="Payment method ID for charges"),
    effective_immediately: bool = Body(True, description="Apply change immediately"),
    current_user: User = Depends(get_current_user),
    billing_service: EnhancedBillingService = Depends(get_enhanced_billing_service)
):
    """Change user's subscription plan with prorated billing"""
    try:
        result = billing_service.change_subscription_plan(
            user_id=current_user.id,
            new_plan_id=new_plan_id,
            payment_method_id=payment_method_id,
            effective_immediately=effective_immediately
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to change subscription plan")
            )
        
        return {
            "success": True,
            "message": "Subscription plan changed successfully",
            "calculation": {
                "prorated_amount": float(result["calculation"].prorated_amount),
                "description": result["calculation"].description,
                "effective_date": result["calculation"].effective_date.isoformat(),
                "next_billing_date": result["calculation"].next_billing_date.isoformat()
            },
            "payment_required": result["calculation"].prorated_amount > 0,
            "payment_result": result.get("payment")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change subscription plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to change subscription plan")


@router.get("/subscription/preview-change")
async def preview_plan_change(
    new_plan_id: str = Query(..., description="New subscription plan ID"),
    effective_date: Optional[datetime] = Query(None, description="Effective date for change"),
    current_user: User = Depends(get_current_user),
    billing_service: EnhancedBillingService = Depends(get_enhanced_billing_service)
):
    """Preview prorated billing calculation for plan change"""
    try:
        calculation = billing_service.calculate_prorated_billing(
            user_id=current_user.id,
            new_plan_id=new_plan_id,
            effective_date=effective_date
        )
        
        return {
            "old_plan_credit": float(calculation.old_plan_credit),
            "new_plan_cost": float(calculation.new_plan_cost),
            "prorated_amount": float(calculation.prorated_amount),
            "effective_date": calculation.effective_date.isoformat(),
            "next_billing_date": calculation.next_billing_date.isoformat(),
            "description": calculation.description,
            "requires_payment": calculation.prorated_amount > 0,
            "provides_credit": calculation.prorated_amount < 0
        }
        
    except Exception as e:
        logger.error(f"Failed to preview plan change: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate plan change preview")


@router.post("/usage/track")
async def track_usage(
    usage_type: str = Body(..., description="Type of usage (sms_sent, voice_minutes, etc.)"),
    quantity: int = Body(1, description="Usage quantity"),
    resource_id: Optional[str] = Body(None, description="Associated resource ID"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata"),
    current_user: User = Depends(get_current_user),
    billing_service: EnhancedBillingService = Depends(get_enhanced_billing_service)
):
    """Track usage and check for alerts"""
    try:
        from models.subscription_models import UsageType
        
        # Convert string to enum
        try:
            usage_type_enum = UsageType(usage_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid usage type: {usage_type}")
        
        result = billing_service.track_usage(
            user_id=current_user.id,
            usage_type=usage_type_enum,
            quantity=quantity,
            resource_id=resource_id,
            metadata=metadata
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to track usage")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to track usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to track usage")


@router.get("/usage/alerts")
async def get_usage_alerts(
    current_user: User = Depends(get_current_user),
    billing_service: EnhancedBillingService = Depends(get_enhanced_billing_service)
):
    """Get current usage alerts"""
    try:
        alerts = billing_service.check_usage_alerts(current_user.id)
        
        return {
            "alerts": [
                {
                    "usage_type": alert.usage_type.value,
                    "current_usage": alert.current_usage,
                    "limit": alert.limit,
                    "percentage": alert.percentage,
                    "threshold": alert.threshold,
                    "alert_level": alert.alert_level,
                    "message": f"{alert.usage_type.value.replace('_', ' ').title()} usage at {alert.percentage:.1f}%"
                }
                for alert in alerts
            ],
            "total_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a.alert_level == "critical"]),
            "exceeded_alerts": len([a for a in alerts if a.alert_level == "exceeded"])
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage alerts")


@router.get("/forecast")
async def get_billing_forecast(
    forecast_days: int = Query(30, ge=1, le=90, description="Number of days to forecast"),
    current_user: User = Depends(get_current_user),
    billing_service: EnhancedBillingService = Depends(get_enhanced_billing_service)
):
    """Get billing forecast based on usage patterns"""
    try:
        forecast = billing_service.generate_billing_forecast(
            user_id=current_user.id,
            forecast_days=forecast_days
        )
        
        return {
            "forecast_period_days": forecast_days,
            "current_period_cost": float(forecast.current_period_cost),
            "projected_monthly_cost": float(forecast.projected_monthly_cost),
            "projected_overage_cost": float(forecast.projected_overage_cost),
            "potential_savings": max(0, float(forecast.current_period_cost - forecast.projected_monthly_cost)),
            "usage_trends": forecast.usage_trend,
            "recommendations": forecast.recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate billing forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate billing forecast")


@router.get("/summary")
async def get_billing_summary(
    current_user: User = Depends(get_current_user),
    billing_service: EnhancedBillingService = Depends(get_enhanced_billing_service)
):
    """Get comprehensive billing summary"""
    try:
        summary = billing_service.get_billing_summary(current_user.id)
        
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get billing summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve billing summary")


@router.get("/payments/history")
async def get_payment_history(
    limit: int = Query(10, ge=1, le=100, description="Number of payments to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    status: Optional[str] = Query(None, description="Filter by payment status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment history for user"""
    try:
        from models.subscription_models import Payment, PaymentStatus
        from sqlalchemy import desc
        
        query = db.query(Payment).filter(Payment.user_id == current_user.id)
        
        if status:
            try:
                status_enum = PaymentStatus(status.lower())
                query = query.filter(Payment.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid payment status: {status}")
        
        total_count = query.count()
        payments = query.order_by(desc(Payment.created_at)).offset(offset).limit(limit).all()
        
        return {
            "payments": [
                {
                    "id": payment.id,
                    "amount": float(payment.amount),
                    "currency": payment.currency,
                    "status": payment.status.value,
                    "payment_method": payment.payment_method,
                    "description": payment.description,
                    "invoice_number": payment.invoice_number,
                    "billing_period_start": payment.billing_period_start.isoformat() if payment.billing_period_start else None,
                    "billing_period_end": payment.billing_period_end.isoformat() if payment.billing_period_end else None,
                    "created_at": payment.created_at.isoformat(),
                    "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                    "failure_message": payment.failure_message
                }
                for payment in payments
            ],
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get payment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment history")


@router.get("/gateways/status")
async def get_gateway_status():
    """Get status of all payment gateways"""
    try:
        status = payment_gateway_factory.get_gateway_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get gateway status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve gateway status")


@router.post("/subscription/cancel")
async def cancel_subscription(
    reason: Optional[str] = Body(None, description="Cancellation reason"),
    cancel_immediately: bool = Body(False, description="Cancel immediately vs at period end"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel user's subscription"""
    try:
        from models.subscription_models import UserSubscription, SubscriptionStatus
        from sqlalchemy import and_
        
        subscription = db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == current_user.id,
                UserSubscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        if cancel_immediately:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
        else:
            subscription.cancel_at_period_end = True
        
        subscription.cancellation_reason = reason
        subscription.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Send notification
        notification_service = NotificationService()
        await notification_service.send_billing_notification(
            user_id=current_user.id,
            event_type="subscription_cancelled",
            details={
                "plan_name": subscription.plan_config.display_name,
                "cancel_immediately": cancel_immediately,
                "effective_date": (
                    subscription.cancelled_at.isoformat() if cancel_immediately
                    else subscription.end_date.isoformat()
                ),
                "reason": reason
            }
        )
        
        return {
            "success": True,
            "message": "Subscription cancelled successfully",
            "cancel_immediately": cancel_immediately,
            "effective_date": (
                subscription.cancelled_at.isoformat() if cancel_immediately
                else subscription.end_date.isoformat()
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")