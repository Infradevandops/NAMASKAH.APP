#!/usr/bin/env python3
"""
SMS Service for namaskah Platform
Handles SMS sending and receiving functionality
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service wrapper for different providers"""

    def __init__(self, provider_client=None):
        self.provider_client = provider_client

    async def send_sms(
        self, from_number: str, to_number: str, message: str
    ) -> Dict[str, Any]:
        """Send SMS using configured provider"""
        try:
            if not self.provider_client:
                # Import here to avoid circular imports
                from main import twilio_client

                self.provider_client = twilio_client

            if not self.provider_client:
                raise Exception("SMS provider not configured")

            result = self.provider_client.messages.create(
                body=message, from_=from_number, to=to_number
            )

            logger.info(
                f"SMS sent from {from_number} to {to_number}. SID: {result.sid}"
            )

            return {
                "success": True,
                "message_sid": result.sid,
                "from_number": from_number,
                "to_number": to_number,
                "status": "sent",
            }

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return {"success": False, "error": str(e)}
