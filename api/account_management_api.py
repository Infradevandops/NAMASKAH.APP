#!/usr/bin/env python3
"""
Account Management API for Namaskah.App
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from auth.security import hash_password, verify_password, is_strong_password
from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.user_models import User
from services.email_service import EmailService

router = APIRouter(prefix="/api/account", tags=["Account Management"])

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    full_name: str = None
    email: EmailStr = None

class AccountResponse(BaseModel):
    message: str
    success: bool

@router.put("/change-password", response_model=AccountResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password with current password verification"""
    
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    is_valid, error_msg = is_strong_password(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    current_user.hashed_password = hash_password(request.new_password)
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return AccountResponse(
        message="Password changed successfully",
        success=True
    )

@router.put("/profile", response_model=AccountResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    
    updated = False
    
    if request.full_name is not None:
        current_user.full_name = request.full_name.strip()
        updated = True
    
    if request.email is not None:
        # Check if email already exists
        existing_user = db.query(User).filter(
            User.email == request.email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        
        current_user.email = request.email
        current_user.is_verified = False  # Require re-verification
        updated = True
    
    if updated:
        current_user.updated_at = datetime.utcnow()
        db.commit()
        
        return AccountResponse(
            message="Profile updated successfully",
            success=True
        )
    
    return AccountResponse(
        message="No changes made",
        success=True
    )

@router.post("/deactivate", response_model=AccountResponse)
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate user account (soft delete)"""
    
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return AccountResponse(
        message="Account deactivated successfully",
        success=True
    )

@router.post("/reactivate", response_model=AccountResponse)
async def reactivate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reactivate user account"""
    
    current_user.is_active = True
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return AccountResponse(
        message="Account reactivated successfully",
        success=True
    )

@router.get("/security-settings")
async def get_security_settings(
    current_user: User = Depends(get_current_user)
):
    """Get account security settings and status"""
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "email_verified": current_user.is_verified,
        "account_active": current_user.is_active,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
        "password_last_changed": current_user.updated_at,
        "security_features": {
            "email_verification": current_user.is_verified,
            "strong_password": True,  # Enforced on change
            "account_recovery": True  # Password reset available
        }
    }