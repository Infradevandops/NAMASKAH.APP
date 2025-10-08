#!/usr/bin/env python3
"""
Google OAuth 2.0 Authentication API
"""
import os
import secrets
import logging
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx

from auth.security import create_access_token, create_refresh_token
from core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/google", tags=["google_oauth"])

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your_google_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your_google_client_secret")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

# Google OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

class GoogleTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: int
    user: dict

@router.get("/login")
async def google_login():
    """
    Initiate Google OAuth 2.0 login flow
    """
    # Check if Google OAuth is configured
    if GOOGLE_CLIENT_ID == "your_google_client_id":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": "Google OAuth not configured",
                "message": "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables",
                "setup_instructions": {
                    "1": "Go to Google Cloud Console",
                    "2": "Create OAuth 2.0 credentials",
                    "3": "Set environment variables: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET",
                    "4": "Configure redirect URI: " + GOOGLE_REDIRECT_URI
                }
            }
        )
    
    # Generate state parameter for security
    state = secrets.token_urlsafe(32)
    
    # Build Google OAuth URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "scope": "openid email profile",
        "response_type": "code",
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    
    return {
        "auth_url": auth_url,
        "state": state,
        "message": "Redirect user to auth_url to complete Google OAuth flow"
    }

@router.get("/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth 2.0 callback
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_data = {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI
            }
            
            token_response = await client.post(GOOGLE_TOKEN_URL, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Get user info from Google
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            user_response = await client.get(GOOGLE_USER_INFO_URL, headers=headers)
            user_response.raise_for_status()
            google_user = user_response.json()
            
            # Create or update user in database
            user_data = await create_or_update_google_user(db, google_user)
            
            # Generate our own JWT tokens
            access_token = create_access_token(data={"sub": user_data["email"]})
            refresh_token = create_refresh_token(data={"sub": user_data["email"]})
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 900,  # 15 minutes
                "user": user_data,
                "google_tokens": {
                    "access_token": tokens.get("access_token"),
                    "refresh_token": tokens.get("refresh_token"),
                    "expires_in": tokens.get("expires_in")
                }
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Google OAuth token exchange failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code for tokens"
        )
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth authentication failed"
        )

@router.post("/token")
async def google_token_exchange(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Exchange Google ID token for application tokens
    """
    try:
        body = await request.json()
        id_token = body.get("id_token")
        
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID token required"
            )
        
        # Verify Google ID token
        async with httpx.AsyncClient() as client:
            verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            response = await client.get(verify_url)
            response.raise_for_status()
            token_info = response.json()
            
            # Verify token audience
            if token_info.get("aud") != GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token audience"
                )
            
            # Create user data from token
            google_user = {
                "id": token_info.get("sub"),
                "email": token_info.get("email"),
                "name": token_info.get("name"),
                "picture": token_info.get("picture"),
                "verified_email": token_info.get("email_verified", False)
            }
            
            # Create or update user
            user_data = await create_or_update_google_user(db, google_user)
            
            # Generate JWT tokens
            access_token = create_access_token(data={"sub": user_data["email"]})
            refresh_token = create_refresh_token(data={"sub": user_data["email"]})
            
            return GoogleTokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=900,
                user=user_data
            )
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google ID token"
        )
    except Exception as e:
        logger.error(f"Google token exchange error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token exchange failed"
        )

async def create_or_update_google_user(db: Session, google_user: dict) -> dict:
    """
    Create or update user from Google OAuth data
    """
    try:
        import sqlite3
        import uuid
        
        # Connect to database
        conn = sqlite3.connect('namaskah.db')
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id, email, username, full_name, role FROM users WHERE email = ?', 
                      (google_user["email"],))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Update existing user
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, is_verified = 1, google_id = ?
                WHERE email = ?
            ''', (google_user.get("name", ""), google_user.get("id"), google_user["email"]))
            
            user_data = {
                "id": existing_user[0],
                "email": existing_user[1],
                "username": existing_user[2],
                "full_name": google_user.get("name", existing_user[3]),
                "role": existing_user[4],
                "is_verified": True,
                "auth_provider": "google"
            }
        else:
            # Create new user
            user_id = str(uuid.uuid4())
            username = google_user["email"].split("@")[0]
            
            cursor.execute('''
                INSERT INTO users (id, email, username, hashed_password, full_name, is_active, is_verified, role, google_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, google_user["email"], username, "", 
                  google_user.get("name", ""), 1, 1, "user", google_user.get("id")))
            
            user_data = {
                "id": user_id,
                "email": google_user["email"],
                "username": username,
                "full_name": google_user.get("name", ""),
                "role": "user",
                "is_verified": True,
                "auth_provider": "google"
            }
        
        conn.commit()
        conn.close()
        
        logger.info(f"Google user created/updated: {google_user['email']}")
        return user_data
        
    except Exception as e:
        logger.error(f"Failed to create/update Google user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )

@router.get("/config")
async def google_oauth_config():
    """
    Get Google OAuth configuration status
    """
    is_configured = (
        GOOGLE_CLIENT_ID != "your_google_client_id" and
        GOOGLE_CLIENT_SECRET != "your_google_client_secret"
    )
    
    return {
        "configured": is_configured,
        "client_id": GOOGLE_CLIENT_ID if is_configured else "Not configured",
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "scopes": ["openid", "email", "profile"],
        "setup_required": not is_configured,
        "setup_instructions": {
            "1": "Go to Google Cloud Console (https://console.cloud.google.com/)",
            "2": "Create a new project or select existing project",
            "3": "Enable Google+ API",
            "4": "Create OAuth 2.0 credentials",
            "5": "Set authorized redirect URI: " + GOOGLE_REDIRECT_URI,
            "6": "Set environment variables: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET"
        } if not is_configured else None
    }

@router.get("/health")
async def google_oauth_health():
    """
    Health check for Google OAuth service
    """
    is_configured = (
        GOOGLE_CLIENT_ID != "your_google_client_id" and
        GOOGLE_CLIENT_SECRET != "your_google_client_secret"
    )
    
    return {
        "status": "configured" if is_configured else "not_configured",
        "service": "google_oauth",
        "version": "1.0.0",
        "endpoints": [
            "/api/auth/google/login",
            "/api/auth/google/callback", 
            "/api/auth/google/token",
            "/api/auth/google/config"
        ]
    }