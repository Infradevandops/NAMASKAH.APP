#!/usr/bin/env python3
"""
JWT Authentication Middleware for FastAPI
"""
import logging
from datetime import datetime
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from auth.security import hash_api_key, verify_token
from core.database import SessionLocal
from models.user_models import APIKey, User

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle JWT authentication for protected routes
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/refresh",
            "/static",
            "/",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and validate authentication if required
        """
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._unauthorized_response("Missing authorization header")

        # Validate Bearer token format
        if not auth_header.startswith("Bearer "):
            return self._unauthorized_response("Invalid authorization header format")

        token = auth_header.split(" ")[1]

        # Validate token and get user
        user = await self._validate_token(token)
        if not user:
            return self._unauthorized_response("Invalid or expired token")

        # Add user to request state
        request.state.current_user = user

        # Continue with the request
        response = await call_next(request)
        return response

    async def _validate_token(self, token: str) -> Optional[User]:
        """
        Validate JWT token or API key and return user
        """
        db = SessionLocal()
        try:
            # Try JWT token first
            payload = verify_token(token, "access")
            if payload:
                user_id = payload.get("sub")
                user = (
                    db.query(User)
                    .filter(User.id == user_id, User.is_active == True)
                    .first()
                )
                if user:
                    return user

            # Try API key
            api_key_hash = hash_api_key(token)
            api_key_record = (
                db.query(APIKey)
                .filter(APIKey.key_hash == api_key_hash, APIKey.is_active == True)
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

                user = (
                    db.query(User)
                    .filter(User.id == api_key_record.user_id, User.is_active == True)
                    .first()
                )
                if user:
                    return user

            return None

        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
        finally:
            db.close()

    def _unauthorized_response(self, detail: str) -> Response:
        """
        Return unauthorized response
        """
        return Response(
            content=f'{{"detail": "{detail}"}}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            media_type="application/json",
        )


class SessionManager:
    """
    Manages user sessions and refresh tokens
    """

    def __init__(self, db: Session):
        self.db = db

    async def create_session(
        self,
        user_id: str,
        refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Create a new user session
        """
        try:
            from datetime import timedelta

            from models.user_models import Session as UserSession

            session = UserSession(
                user_id=user_id,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(days=7),
                user_agent=user_agent,
                ip_address=ip_address,
            )

            self.db.add(session)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            self.db.rollback()
            return False

    async def validate_session(self, refresh_token: str) -> Optional[User]:
        """
        Validate refresh token and return associated user
        """
        try:
            from models.user_models import Session as UserSession

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
                return None

            user = (
                self.db.query(User)
                .filter(User.id == session.user_id, User.is_active == True)
                .first()
            )

            if user:
                # Update session last used
                session.last_used = datetime.utcnow()
                self.db.commit()

            return user

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None

    async def invalidate_session(self, refresh_token: str) -> bool:
        """
        Invalidate a session (logout)
        """
        try:
            from models.user_models import Session as UserSession

            session = (
                self.db.query(UserSession)
                .filter(UserSession.refresh_token == refresh_token)
                .first()
            )

            if session:
                session.is_active = False
                self.db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            self.db.rollback()
            return False

    async def invalidate_all_user_sessions(self, user_id: str) -> bool:
        """
        Invalidate all sessions for a user
        """
        try:
            from models.user_models import Session as UserSession

            sessions = (
                self.db.query(UserSession)
                .filter(UserSession.user_id == user_id, UserSession.is_active == True)
                .all()
            )

            for session in sessions:
                session.is_active = False

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate user sessions: {e}")
            self.db.rollback()
            return False

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        """
        try:
            from models.user_models import Session as UserSession

            expired_sessions = (
                self.db.query(UserSession)
                .filter(UserSession.expires_at < datetime.utcnow())
                .all()
            )

            count = len(expired_sessions)

            for session in expired_sessions:
                session.is_active = False

            self.db.commit()
            logger.info(f"Cleaned up {count} expired sessions")
            return count

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            self.db.rollback()
            return 0


# Dependency function to get current user from middleware
def get_current_user_from_middleware(request: Request) -> User:
    """
    Get current user from middleware state
    """
    if not hasattr(request.state, "current_user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    return request.state.current_user


# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # In production, use Redis

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check rate limits before processing request
        """
        client_ip = request.client.host if request.client else "127.0.0.1"
        current_time = datetime.utcnow()

        # Clean old entries (simple cleanup)
        self._cleanup_old_entries(current_time)

        # Check current rate
        if client_ip in self.request_counts:
            if len(self.request_counts[client_ip]) >= self.requests_per_minute:
                return Response(
                    content='{"detail": "Rate limit exceeded"}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                )

        # Add current request
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []

        self.request_counts[client_ip].append(current_time)

        # Continue with request
        return await call_next(request)

    def _cleanup_old_entries(self, current_time: datetime):
        """
        Remove entries older than 1 minute
        """
        cutoff_time = current_time.timestamp() - 60  # 1 minute ago

        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = [
                req_time
                for req_time in self.request_counts[ip]
                if req_time.timestamp() > cutoff_time
            ]

            # Remove empty entries
            if not self.request_counts[ip]:
                del self.request_counts[ip]
