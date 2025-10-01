#!/usr/bin/env python3
"""
Webhook API endpoints for external service integrations
"""
import hashlib
import hmac
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel

from services.notification_service import NotificationService
from services.billing_service import BillingService
from core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

notification_service = NotificationService()

class WebhookEvent(BaseModel):
    event_type: str
    data: Dict[str, Any]
    timestamp: str

# Stripe Webhook
@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        
        # Verify webhook signature (simplified)
        if not _verify_stripe_signature(payload, stripe_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        event = json.loads(payload)
        event_type = event.get("type")
        
        if event_type == "payment_intent.succeeded":
            await _handle_payment_success(event["data"]["object"])
        elif event_type == "payment_intent.payment_failed":
            await _handle_payment_failed(event["data"]["object"])
        elif event_type == "invoice.payment_succeeded":
            await _handle_subscription_payment(event["data"]["object"])
            
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

# SMS Service Webhook
@router.post("/sms/delivery")
async def sms_delivery_webhook(request: Request):
    """Handle SMS delivery status updates"""
    try:
        payload = await request.json()
        
        message_id = payload.get("message_id")
        status = payload.get("status")  # delivered, failed, pending
        
        if status == "delivered":
            await _handle_sms_delivered(message_id)
        elif status == "failed":
            await _handle_sms_failed(message_id, payload.get("error"))
            
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"SMS webhook error: {e}")
        raise HTTPException(status_code=500, detail="SMS webhook failed")

# TextVerified Webhook
@router.post("/textverified")
async def textverified_webhook(request: Request):
    """Handle TextVerified service callbacks"""
    try:
        payload = await request.json()
        
        # TextVerified webhook payload structure
        verification_id = payload.get("id")
        status = payload.get("status")  # pending, completed, expired, cancelled
        phone_number = payload.get("number")
        service = payload.get("service")
        messages = payload.get("messages", [])
        
        if status == "completed" and messages:
            # Extract verification code from latest message
            latest_message = messages[-1].get("text", "")
            code = _extract_verification_code(latest_message)
            await _handle_verification_completed(verification_id, code, service)
        elif status == "expired":
            await _handle_verification_expired(verification_id, service)
        elif messages:
            # New SMS received
            for msg in messages:
                await _handle_verification_sms(verification_id, msg.get("text"), service)
            
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"TextVerified webhook error: {e}")
        raise HTTPException(status_code=500, detail="TextVerified webhook failed")

# Helper functions
def _verify_stripe_signature(payload: bytes, signature: str) -> bool:
    """Verify Stripe webhook signature"""
    # Simplified - implement proper Stripe signature verification
    return True  # TODO: Implement actual verification

async def _handle_payment_success(payment_intent: Dict):
    """Handle successful payment"""
    user_id = payment_intent.get("metadata", {}).get("user_id")
    amount = payment_intent.get("amount") / 100  # Convert from cents
    
    await notification_service.send_payment_notification(
        user_id=user_id,
        payment_status="succeeded",
        details={"amount": amount, "currency": payment_intent.get("currency")}
    )

async def _handle_payment_failed(payment_intent: Dict):
    """Handle failed payment"""
    user_id = payment_intent.get("metadata", {}).get("user_id")
    
    await notification_service.send_payment_notification(
        user_id=user_id,
        payment_status="failed",
        details={"error": payment_intent.get("last_payment_error", {}).get("message")}
    )

async def _handle_subscription_payment(invoice: Dict):
    """Handle subscription payment"""
    customer_id = invoice.get("customer")
    amount = invoice.get("amount_paid") / 100
    
    # Update user subscription status
    logger.info(f"Subscription payment received: {customer_id} - ${amount}")

async def _handle_sms_delivered(message_id: str):
    """Handle SMS delivery confirmation"""
    logger.info(f"SMS delivered: {message_id}")

async def _handle_sms_failed(message_id: str, error: str):
    """Handle SMS delivery failure"""
    logger.error(f"SMS failed: {message_id} - {error}")

def _extract_verification_code(message: str) -> str:
    """Extract verification code from SMS message"""
    import re
    # Common patterns for verification codes
    patterns = [
        r'\b(\d{4,8})\b',  # 4-8 digit codes
        r'code[:\s]*(\d+)',  # "code: 123456"
        r'verification[:\s]*(\d+)',  # "verification: 123456"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""

async def _handle_verification_sms(verification_id: str, message: str, service: str):
    """Handle verification SMS received"""
    code = _extract_verification_code(message)
    logger.info(f"SMS received for {verification_id} ({service}): {message[:50]}...")
    
    # Update verification in database
    from services.verification_service import VerificationService
    # TODO: Update verification with new message

async def _handle_verification_completed(verification_id: str, code: str, service: str):
    """Handle verification completion"""
    logger.info(f"Verification completed: {verification_id} ({service}) - Code: {code}")
    
    # Update verification status and notify user
    await notification_service.send_verification_completed(
        user_id="system",  # TODO: Get actual user_id from verification
        service_name=service,
        verification_code=code
    )

async def _handle_verification_expired(verification_id: str, service: str):
    """Handle verification expiration"""
    logger.info(f"Verification expired: {verification_id} ({service})")
    
    await notification_service.send_verification_expired(
        user_id="system",  # TODO: Get actual user_id from verification
        service_name=service
    )