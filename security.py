#!/usr/bin/env python3
"""
Security utilities for namaskah Platform
Handles input sanitization, CSRF protection, and security headers
"""
import html
import re
import secrets
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer


class SecurityUtils:
    """Security utilities for input validation and sanitization"""

    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        if not text:
            return ""
        return html.escape(text, quote=True)

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format"""
        pattern = r"^\+?[1-9]\d{1,14}$"
        return bool(re.match(pattern, phone.replace(" ", "").replace("-", "")))

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))


class CSRFProtection:
    """CSRF token generation and validation"""

    def __init__(self):
        self.tokens = {}

    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session"""
        token = secrets.token_urlsafe(32)
        self.tokens[session_id] = token
        return token

    def validate_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token"""
        return self.tokens.get(session_id) == token


# Global instances
security_utils = SecurityUtils()
csrf_protection = CSRFProtection()
