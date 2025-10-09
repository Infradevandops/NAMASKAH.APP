#!/usr/bin/env python3
"""
Email Verification API
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from core.database import get_db
from models.email_verification_models import EmailVerificationRequest, EmailVerificationConfirm, EmailVerificationResponse
from models.user_models import User
from services.email_service import email_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["email_verification"])

@router.post("/send-verification", response_model=EmailVerificationResponse)
async def send_verification_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Send email verification to user"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Send verification email
        token = await email_service.send_verification_email(
            db=db,
            user_id=str(user.id),
            email=user.email
        )
        
        return EmailVerificationResponse(
            message="Verification email sent successfully",
            email=user.email,
            expires_in=86400  # 24 hours
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )

@router.post("/verify-email")
async def verify_email(
    request: EmailVerificationConfirm,
    db: Session = Depends(get_db)
):
    """Verify email with token"""
    try:
        result = await email_service.verify_email_token(db, request.token)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        return {
            "message": "Email verified successfully",
            "user_id": result["user_id"],
            "email": result["email"],
            "verified_at": result["verified_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )

@router.get("/verify-email")
async def verify_email_get(token: str, db: Session = Depends(get_db)):
    """Verify email via GET request (for email links)"""
    try:
        result = await email_service.verify_email_token(db, token)
        
        if not result:
            return {"message": "Invalid or expired verification token", "success": False}
        
        return {
            "message": "Email verified successfully! You can now close this page.",
            "success": True,
            "email": result["email"]
        }
        
    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        return {"message": "Email verification failed", "success": False}

@router.get("/verification-status/{email}")
async def get_verification_status(email: str, db: Session = Depends(get_db)):
    """Check email verification status"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "email": user.email,
            "is_verified": user.is_verified,
            "verified_at": user.email_verified_at.isoformat() if user.email_verified_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check verification status"
        )