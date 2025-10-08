#!/usr/bin/env python3
"""
Auth 2.0 API Endpoints with Refresh Token Support
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from core.database import get_db
from models.refresh_token_models import (
    TokenRefreshRequest, TokenRefreshResponse,
    LogoutRequest, LogoutAllRequest
)
from services.refresh_token_service import get_refresh_token_service
from services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/v2", tags=["auth_v2"])

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    Implements token rotation for security
    """
    try:
        refresh_service = get_refresh_token_service(db)
        
        # Extract device info from request
        device_info = {
            "user_agent": http_request.headers.get("user-agent"),
            "ip_address": http_request.client.host,
            "timestamp": str(http_request.headers.get("x-timestamp"))
        }
        
        # Refresh tokens
        result = refresh_service.refresh_access_token(
            request.refresh_token, 
            device_info
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        access_token, new_refresh_token = result
        
        return TokenRefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=900  # 15 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout_user(
    request: LogoutRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Secure logout - revokes refresh token and blacklists access token
    """
    try:
        refresh_service = get_refresh_token_service(db)
        
        # Revoke refresh token
        revoked = refresh_service.revoke_refresh_token(
            request.refresh_token, 
            reason="user_logout"
        )
        
        if not revoked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token"
            )
        
        # Try to blacklist access token if provided
        auth_header = http_request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.split(" ")[1]
            refresh_service.blacklist_access_token(access_token, "user_logout")
        
        return {"message": "Logged out successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/logout-all")
async def logout_all_devices(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout from all devices - revokes all refresh tokens for user
    """
    try:
        refresh_service = get_refresh_token_service(db)
        
        # Revoke all user tokens
        revoked_count = refresh_service.revoke_all_user_tokens(
            str(current_user.id), 
            reason="logout_all_devices"
        )
        
        return {
            "message": f"Logged out from {revoked_count} devices successfully",
            "revoked_tokens": revoked_count
        }
        
    except Exception as e:
        logger.error(f"Logout all error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout from all devices failed"
        )

@router.get("/sessions")
async def get_active_sessions(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active sessions (refresh tokens) for current user
    """
    try:
        refresh_service = get_refresh_token_service(db)
        
        active_tokens = refresh_service.get_user_active_tokens(str(current_user.id))
        
        return {
            "active_sessions": len(active_tokens),
            "sessions": active_tokens
        }
        
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active sessions"
        )

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a specific session (refresh token)
    """
    try:
        from models.refresh_token_models import RefreshToken
        
        # Find the specific token
        token = db.query(RefreshToken).filter(
            RefreshToken.id == session_id,
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_active == True
        ).first()
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Revoke the token
        refresh_service = get_refresh_token_service(db)
        token.is_active = False
        token.revoked_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )

@router.post("/cleanup")
async def cleanup_expired_tokens(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to cleanup expired tokens
    Requires admin role
    """
    try:
        # Check if user is admin
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        refresh_service = get_refresh_token_service(db)
        result = refresh_service.cleanup_expired_tokens()
        
        return {
            "message": "Token cleanup completed",
            "cleaned_up": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token cleanup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token cleanup failed"
        )

@router.get("/health")
async def auth_v2_health():
    """
    Health check for Auth 2.0 service
    """
    return {
        "status": "healthy",
        "service": "auth_v2",
        "version": "2.0.0",
        "features": [
            "refresh_tokens",
            "token_rotation", 
            "secure_logout",
            "session_management",
            "token_blacklisting"
        ]
    }