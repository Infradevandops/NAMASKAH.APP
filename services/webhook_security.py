#!/usr/bin/env python3
"""
Webhook security utilities for signature verification
"""
import hashlib
import hmac
import os
from typing import Optional

class WebhookSecurity:
    """Webhook signature verification utilities"""
    
    @staticmethod
    def verify_stripe_signature(payload: bytes, signature: str, secret: Optional[str] = None) -> bool:
        """Verify Stripe webhook signature"""
        if not secret:
            secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not secret or not signature:
            return False
            
        try:
            # Extract timestamp and signature from header
            elements = signature.split(',')
            timestamp = None
            signatures = []
            
            for element in elements:
                key, value = element.split('=', 1)
                if key == 't':
                    timestamp = value
                elif key == 'v1':
                    signatures.append(value)
            
            if not timestamp or not signatures:
                return False
            
            # Create expected signature
            signed_payload = f"{timestamp}.{payload.decode()}"
            expected_signature = hmac.new(
                secret.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return any(hmac.compare_digest(expected_signature, sig) for sig in signatures)
            
        except Exception:
            return False
    
    @staticmethod
    def verify_twilio_signature(payload: bytes, signature: str, url: str, secret: Optional[str] = None) -> bool:
        """Verify Twilio webhook signature"""
        if not secret:
            secret = os.getenv("TWILIO_AUTH_TOKEN")
        
        if not secret or not signature:
            return False
            
        try:
            # Twilio signature verification
            expected_signature = hmac.new(
                secret.encode(),
                f"{url}{payload.decode()}".encode(),
                hashlib.sha1
            ).digest()
            
            import base64
            expected_signature_b64 = base64.b64encode(expected_signature).decode()
            
            return hmac.compare_digest(expected_signature_b64, signature)
            
        except Exception:
            return False
    
    @staticmethod
    def verify_generic_signature(payload: bytes, signature: str, secret: str, algorithm: str = "sha256") -> bool:
        """Generic webhook signature verification"""
        try:
            hash_func = getattr(hashlib, algorithm)
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hash_func
            ).hexdigest()
            
            # Handle different signature formats
            if signature.startswith(f"{algorithm}="):
                signature = signature[len(f"{algorithm}="):]
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception:
            return False