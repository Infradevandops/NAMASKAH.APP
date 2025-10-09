#!/usr/bin/env python3
"""
Email Service for sending verification emails
"""
import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from models.email_verification_models import EmailVerificationToken
from models.user_models import User

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.email_provider = os.getenv("EMAIL_PROVIDER", "mock")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@namaskah.app")
        
    async def send_verification_email(self, db: Session, user_id: str, email: str) -> str:
        """Generate token and send verification email"""
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Save token to database
        verification_token = EmailVerificationToken(
            user_id=user_id,
            email=email,
            token=token,
            expires_at=expires_at
        )
        db.add(verification_token)
        db.commit()
        
        # Send email
        if self.email_provider == "sendgrid" and self.sendgrid_api_key:
            await self._send_sendgrid_email(email, token)
        else:
            await self._send_mock_email(email, token)
            
        return token
    
    async def verify_email_token(self, db: Session, token: str) -> Optional[dict]:
        """Verify email token and activate user"""
        verification = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token,
            EmailVerificationToken.is_used == False
        ).first()
        
        if not verification or verification.is_expired():
            return None
            
        # Mark token as used
        verification.is_used = True
        verification.used_at = datetime.utcnow()
        
        # Update user as verified
        user = db.query(User).filter(User.id == verification.user_id).first()
        if user:
            user.is_verified = True
            user.email_verified_at = datetime.utcnow()
            
        db.commit()
        
        return {
            "user_id": str(verification.user_id),
            "email": verification.email,
            "verified_at": verification.used_at.isoformat()
        }
    
    async def _send_sendgrid_email(self, email: str, token: str):
        """Send email via SendGrid"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={token}"
            
            message = Mail(
                from_email=self.from_email,
                to_emails=email,
                subject="Verify your Namaskah.App email",
                html_content=f"""
                <h2>Welcome to Namaskah.App!</h2>
                <p>Please click the link below to verify your email address:</p>
                <a href="{verification_url}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a>
                <p>Or copy this link: {verification_url}</p>
                <p>This link expires in 24 hours.</p>
                """
            )
            
            response = sg.send(message)
            logger.info(f"Verification email sent to {email}: {response.status_code}")
            
        except Exception as e:
            logger.error(f"SendGrid email failed: {e}")
            await self._send_mock_email(email, token)
    
    async def _send_mock_email(self, email: str, token: str):
        """Mock email sending for development"""
        verification_url = f"http://localhost:8000/api/auth/verify-email?token={token}"
        
        logger.info(f"""
        📧 MOCK EMAIL SENT TO: {email}
        🔗 Verification URL: {verification_url}
        ⏰ Expires: 24 hours
        """)
        
        # Save to file for development
        with open("verification_emails.log", "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} | {email} | {verification_url}\n")

email_service = EmailService()