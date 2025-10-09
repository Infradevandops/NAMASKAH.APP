#!/usr/bin/env python3
"""
Simple Email Verification API
"""
import sqlite3
import secrets
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["email_verification"])

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    token: str

@router.post("/send-verification")
async def send_verification_email(request: EmailVerificationRequest):
    """Send email verification to user"""
    try:
        conn = sqlite3.connect('namaskah.db')
        cursor = conn.cursor()
        
        # Find user by email
        cursor.execute('SELECT id, email, is_verified FROM users WHERE email = ?', (request.email,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user[2]:  # is_verified
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Generate token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Save token
        cursor.execute('''
            INSERT INTO email_verification_tokens 
            (id, user_id, email, token, expires_at, is_used)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (secrets.token_urlsafe(16), user[0], user[1], token, expires_at, 0))
        
        conn.commit()
        conn.close()
        
        # Mock email sending
        verification_url = f"http://localhost:8000/api/auth/verify-email?token={token}"
        logger.info(f"""
        📧 VERIFICATION EMAIL SENT TO: {user[1]}
        🔗 Verification URL: {verification_url}
        ⏰ Expires: 24 hours
        """)
        
        return {
            "message": "Verification email sent successfully",
            "email": user[1],
            "expires_in": 86400,
            "verification_url": verification_url  # For testing
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )

@router.get("/verify-email")
async def verify_email_get(token: str):
    """Verify email via GET request"""
    try:
        conn = sqlite3.connect('namaskah.db')
        cursor = conn.cursor()
        
        # Find token
        cursor.execute('''
            SELECT user_id, email, expires_at, is_used 
            FROM email_verification_tokens 
            WHERE token = ?
        ''', (token,))
        verification = cursor.fetchone()
        
        if not verification:
            return {"message": "Invalid verification token", "success": False}
        
        if verification[3]:  # is_used
            return {"message": "Verification token already used", "success": False}
        
        if datetime.utcnow() > datetime.fromisoformat(verification[2]):
            return {"message": "Verification token expired", "success": False}
        
        # Mark token as used
        cursor.execute('''
            UPDATE email_verification_tokens 
            SET is_used = 1, used_at = ? 
            WHERE token = ?
        ''', (datetime.utcnow(), token))
        
        # Update user as verified
        cursor.execute('''
            UPDATE users 
            SET is_verified = 1, email_verified_at = ? 
            WHERE id = ?
        ''', (datetime.utcnow(), verification[0]))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Email verified successfully! You can now close this page.",
            "success": True,
            "email": verification[1]
        }
        
    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        return {"message": "Email verification failed", "success": False}

@router.post("/verify-email")
async def verify_email_post(request: EmailVerificationConfirm):
    """Verify email via POST request"""
    result = await verify_email_get(request.token)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return result

@router.get("/verification-status/{email}")
async def get_verification_status(email: str):
    """Check email verification status"""
    try:
        conn = sqlite3.connect('namaskah.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT email, is_verified, email_verified_at FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        conn.close()
        
        return {
            "email": user[0],
            "is_verified": bool(user[1]),
            "verified_at": user[2] if user[2] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check verification status"
        )