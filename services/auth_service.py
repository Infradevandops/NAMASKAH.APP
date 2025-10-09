#!/usr/bin/env python3
"""
Authentication Service for namaskah Platform
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.security import (create_access_token, create_refresh_token,
                           generate_api_key, generate_reset_token,
                           generate_verification_token, hash_api_key,
                           hash_password, is_strong_password, verify_api_key,
                           verify_password, verify_token)
from core.database import get_db
from models.user_models import APIKey
from models.user_models import Session as UserSession
from models.user_models import SubscriptionPlan, User, UserRole

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthenticationService:
    """Service for handling user authentication and authorization"""

    def __init__(self, db: Session):
        self.db = db

    async def register_user(
        self, email: str, username: str, password: str, full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a new user
        """
        try:
            # Validate password strength
            is_valid, error_msg = is_strong_password(password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
                )

            # Check if user already exists
            existing_user = (
                self.db.query(User)
                .filter((User.email == email) | (User.username == username))
                .first()
            )

            if existing_user:
                if existing_user.email == email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered",
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken",
                    )

            # Create new user
            hashed_password = hash_password(password)
            verification_token = generate_verification_token()

            user = User(
                email=email,
                username=username,
                hashed_password=hashed_password,
                full_name=full_name,
                email_verification_token=verification_token,
                email_verification_expires=datetime.utcnow() + timedelta(hours=24),
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info(f"User registered successfully: {user.id}")

            return {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "verification_token": verification_token,
                "message": "User registered successfully. Please verify your email.",
            }

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error during registration: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists",
            )
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error during registration: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed",
            )

    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and return tokens
        """
        try:
            # Find user by email
            user = self.db.query(User).filter(User.email == email).first()

            if not user or not verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is deactivated",
                )

            # Create tokens
            access_token = create_access_token({"sub": user.id, "email": user.email})
            refresh_token = create_refresh_token({"sub": user.id})

            # Store refresh token in database
            session = UserSession(
                user_id=user.id,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(days=7),
            )

            self.db.add(session)

            # Update last login
            user.last_login = datetime.utcnow()

            self.db.commit()

            logger.info(f"User authenticated successfully: {user.id}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 900,  # 15 minutes
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "subscription_plan": user.subscription_plan,
                    "is_verified": user.is_verified,
                },
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed",
            )

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        """
        try:
            # Verify refresh token
            payload = verify_token(refresh_token, "refresh")
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            user_id = payload.get("sub")

            # Check if session exists and is active
            session = (
                self.db.query(UserSession)
                .filter(
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow(),
                )
                .first()
            )

            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token",
                )

            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )

            # Create new access token
            access_token = create_access_token({"sub": user.id, "email": user.email})

            # Update session last used
            session.last_used = datetime.utcnow()
            self.db.commit()

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 900,  # 15 minutes
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed",
            )

    async def logout(self, refresh_token: str) -> Dict[str, Any]:
        """
        Logout user by invalidating refresh token
        """
        try:
            session = (
                self.db.query(UserSession)
                .filter(UserSession.refresh_token == refresh_token)
                .first()
            )

            if session:
                session.is_active = False
                self.db.commit()
                logger.info(f"User logged out: {session.user_id}")

            return {"message": "Logged out successfully"}

        except Exception as e:
            logger.error(f"Error during logout: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed",
            )

    async def verify_email(self, token: str) -> Dict[str, Any]:
        """
        Verify user email with verification token
        """
        try:
            user = (
                self.db.query(User)
                .filter(
                    User.email_verification_token == token,
                    User.email_verification_expires > datetime.utcnow(),
                )
                .first()
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification token",
                )

            user.is_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None

            self.db.commit()

            logger.info(f"Email verified for user: {user.id}")

            return {"message": "Email verified successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during email verification: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email verification failed",
            )

    async def create_api_key(
        self, user_id: str, name: str, scopes: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key for user
        """
        try:
            api_key = generate_api_key()
            key_hash = hash_api_key(api_key)

            db_api_key = APIKey(
                user_id=user_id, key_hash=key_hash, name=name, scopes=str(scopes or [])
            )

            self.db.add(db_api_key)
            self.db.commit()
            self.db.refresh(db_api_key)

            logger.info(f"API key created for user: {user_id}")

            return {
                "api_key": api_key,  # Only returned once
                "key_id": db_api_key.id,
                "name": name,
                "created_at": db_api_key.created_at,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key creation failed",
            )


# Dependency functions for FastAPI
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token
    """
    token = credentials.credentials

    # Try JWT token first
    payload = verify_token(token, "access")
    if payload:
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_active:
            return user

    # Try API key
    api_key_record = (
        db.query(APIKey)
        .filter(APIKey.key_hash == hash_api_key(token), APIKey.is_active == True)
        .first()
    )

    if api_key_record:
        # Update API key usage
        api_key_record.last_used = datetime.utcnow()
        api_key_record.total_requests += 1

        # Reset daily counter if needed
        today = datetime.utcnow().date()
        if (
            not api_key_record.last_request_date
            or api_key_record.last_request_date.date() != today
        ):
            api_key_record.requests_today = 1
            api_key_record.last_request_date = datetime.utcnow()
        else:
            api_key_record.requests_today += 1

        db.commit()

        user = db.query(User).filter(User.id == api_key_record.user_id).first()
        if user and user.is_active:
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (additional check for active status)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user
