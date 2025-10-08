#!/usr/bin/env python3
"""
Refresh Token Service for Auth 2.0
"""
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.refresh_token_models import RefreshToken, TokenBlacklist
from auth.security import create_access_token, verify_token
from core.database import get_db

logger = logging.getLogger(__name__)

class RefreshTokenService:
    def __init__(self, db: Session):
        self.db = db
        self.token_expiry_days = 7  # Refresh tokens expire in 7 days
    
    def generate_refresh_token(self, user_id: str, device_info: Optional[Dict[str, Any]] = None) -> Tuple[str, RefreshToken]:
        """Generate a new refresh token"""
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Create refresh token record
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=self.token_expiry_days),
            device_info=device_info or {}
        )
        
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        
        logger.info(f"Generated refresh token for user: {user_id}")
        return token, refresh_token
    
    def verify_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Verify and return refresh token if valid"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        refresh_token = self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_active == True
            )
        ).first()
        
        if not refresh_token:
            logger.warning("Refresh token not found")
            return None
        
        if not refresh_token.is_valid():
            logger.warning(f"Invalid refresh token for user: {refresh_token.user_id}")
            return None
        
        return refresh_token
    
    def refresh_access_token(self, refresh_token_str: str, device_info: Optional[Dict[str, Any]] = None) -> Optional[Tuple[str, str]]:
        """Refresh access token and rotate refresh token"""
        # Verify current refresh token
        current_token = self.verify_refresh_token(refresh_token_str)
        if not current_token:
            return None
        
        user_id = str(current_token.user_id)
        
        # Revoke current refresh token
        current_token.is_active = False
        current_token.revoked_at = datetime.utcnow()
        
        # Generate new tokens
        access_token = create_access_token(data={"sub": user_id})
        new_refresh_token, _ = self.generate_refresh_token(user_id, device_info)
        
        self.db.commit()
        
        logger.info(f"Refreshed tokens for user: {user_id}")
        return access_token, new_refresh_token
    
    def revoke_refresh_token(self, token: str, reason: str = "logout") -> bool:
        """Revoke a specific refresh token"""
        refresh_token = self.verify_refresh_token(token)
        if not refresh_token:
            return False
        
        refresh_token.is_active = False
        refresh_token.revoked_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Revoked refresh token for user: {refresh_token.user_id}, reason: {reason}")
        return True
    
    def revoke_all_user_tokens(self, user_id: str, reason: str = "logout_all") -> int:
        """Revoke all refresh tokens for a user"""
        tokens = self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_active == True
            )
        ).all()
        
        count = 0
        for token in tokens:
            token.is_active = False
            token.revoked_at = datetime.utcnow()
            count += 1
        
        self.db.commit()
        
        logger.info(f"Revoked {count} refresh tokens for user: {user_id}, reason: {reason}")
        return count
    
    def blacklist_access_token(self, access_token: str, reason: str = "logout") -> bool:
        """Add access token to blacklist"""
        try:
            payload = verify_token(access_token, "access")
            if not payload:
                return False
            
            jti = payload.get("jti", hashlib.sha256(access_token.encode()).hexdigest()[:16])
            exp = datetime.fromtimestamp(payload.get("exp", 0))
            
            blacklist_entry = TokenBlacklist(
                token_jti=jti,
                expires_at=exp,
                reason=reason
            )
            
            self.db.add(blacklist_entry)
            self.db.commit()
            
            logger.info(f"Blacklisted access token, reason: {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if access token is blacklisted"""
        blacklist_entry = self.db.query(TokenBlacklist).filter(
            TokenBlacklist.token_jti == jti
        ).first()
        
        return blacklist_entry is not None
    
    def cleanup_expired_tokens(self) -> Dict[str, int]:
        """Clean up expired tokens and blacklist entries"""
        now = datetime.utcnow()
        
        # Clean expired refresh tokens
        expired_refresh = self.db.query(RefreshToken).filter(
            RefreshToken.expires_at < now
        ).count()
        
        self.db.query(RefreshToken).filter(
            RefreshToken.expires_at < now
        ).delete()
        
        # Clean expired blacklist entries
        expired_blacklist = self.db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < now
        ).count()
        
        self.db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < now
        ).delete()
        
        self.db.commit()
        
        result = {
            "expired_refresh_tokens": expired_refresh,
            "expired_blacklist_entries": expired_blacklist
        }
        
        logger.info(f"Cleaned up expired tokens: {result}")
        return result
    
    def get_user_active_tokens(self, user_id: str) -> list:
        """Get all active refresh tokens for a user"""
        tokens = self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_active == True,
                RefreshToken.expires_at > datetime.utcnow()
            )
        ).all()
        
        return [
            {
                "id": str(token.id),
                "created_at": token.created_at,
                "expires_at": token.expires_at,
                "device_info": token.device_info
            }
            for token in tokens
        ]

def get_refresh_token_service(db: Session = None) -> RefreshTokenService:
    """Get refresh token service instance"""
    if db is None:
        db = next(get_db())
    return RefreshTokenService(db)