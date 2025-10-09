#!/usr/bin/env python3
"""
Password Reset API for Namaskah.App
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from auth.security import hash_password, generate_verification_token
from core.database import get_db
from models.user_models import User
from models.password_reset_models import PasswordResetToken
from services.email_service import EmailService

router = APIRouter(prefix="/api/password-reset", tags=["Password Reset"])

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordResetResponse(BaseModel):
    message: str
    success: bool

@router.post("/request", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset - sends email with reset token"""
    
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists - security best practice
        return PasswordResetResponse(
            message="If the email exists, a password reset link has been sent.",
            success=True
        )
    
    # Generate reset token
    reset_token = generate_verification_token()
    
    # Invalidate any existing reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False
    ).update({"used": True, "used_at": datetime.utcnow()})
    
    # Create new reset token
    password_reset = PasswordResetToken.create_token(
        user_id=user.id,
        token=reset_token,
        expires_hours=24
    )
    
    db.add(password_reset)
    db.commit()
    
    # Send reset email
    email_service = EmailService()
    await email_service.send_password_reset_email(
        email=user.email,
        name=user.full_name or user.username,
        reset_token=reset_token
    )
    
    return PasswordResetResponse(
        message="If the email exists, a password reset link has been sent.",
        success=True
    )

@router.post("/confirm", response_model=PasswordResetResponse)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token and set new password"""
    
    # Find reset token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token
    ).first()
    
    if not reset_token or not reset_token.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = hash_password(request.new_password)
    
    # Mark token as used
    reset_token.mark_as_used()
    
    db.commit()
    
    return PasswordResetResponse(
        message="Password has been reset successfully.",
        success=True
    )

@router.get("/verify/{token}")
async def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify if reset token is valid"""
    
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()
    
    if not reset_token or not reset_token.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {
        "valid": True,
        "expires_at": reset_token.expires_at,
        "message": "Token is valid"
    }