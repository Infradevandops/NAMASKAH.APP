#!/usr/bin/env python3
"""
Enhanced Verification Service for CumApp Communication Platform
Handles TextVerified integration with user association, history tracking, and code extraction
"""
import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from core.error_handler import with_error_handling
from core.retry_handler import textverified_retry_decorator
from models.user_models import User
from models.verification_models import VerificationRequest
from services.notification_service import NotificationService
from clients.textverified_client import TextVerifiedClient

logger = logging.getLogger(__name__)


class CodeExtractionService:
    """Service for extracting verification codes from SMS messages"""

    # Common verification code patterns
    CODE_PATTERNS = [
        r"\b(\d{4,8})\b",  # 4-8 digit codes
        r"code[:\s]*(\d{4,8})",  # "code: 123456"
        r"verification[:\s]*(\d{4,8})",  # "verification: 123456"
        r"confirm[:\s]*(\d{4,8})",  # "confirm: 123456"
        r"pin[:\s]*(\d{4,8})",  # "pin: 123456"
        r"otp[:\s]*(\d{4,8})",  # "otp: 123456"
        r"(\d{4,8})\s*is\s*your",  # "123456 is your code"
        r"your\s*code\s*is[:\s]*(\d{4,8})",  # "your code is 123456"
    ]

    # Service-specific patterns for better accuracy
    SERVICE_PATTERNS = {
        "whatsapp": [
            r"WhatsApp[:\s]*(\d{6})",
            r"(\d{6})\s*is\s*your\s*WhatsApp",
        ],
        "google": [
            r"Google[:\s]*(\d{6})",
            r"G-(\d{6})",
            r"(\d{6})\s*is\s*your\s*Google",
        ],
        "telegram": [
            r"Telegram[:\s]*(\d{5})",
            r"(\d{5})\s*is\s*your\s*Telegram",
        ],
        "discord": [
            r"Discord[:\s]*(\d{6})",
            r"(\d{6})\s*is\s*your\s*Discord",
        ],
        "facebook": [
            r"Facebook[:\s]*(\d{5,8})",
            r"(\d{5,8})\s*is\s*your\s*Facebook",
        ],
        "instagram": [
            r"Instagram[:\s]*(\d{6})",
            r"(\d{6})\s*is\s*your\s*Instagram",
        ],
        "twitter": [
            r"Twitter[:\s]*(\d{6})",
            r"(\d{6})\s*is\s*your\s*Twitter",
        ],
        "tiktok": [
            r"TikTok[:\s]*(\d{4,6})",
            r"(\d{4,6})\s*is\s*your\s*TikTok",
        ],
    }

    @classmethod
    def extract_verification_codes(
        cls, message_content: str, service_name: str = None
    ) -> List[str]:
        """
        Extract verification codes from SMS message content

        Args:
            message_content: The SMS message content
            service_name: Optional service name for service-specific patterns

        Returns:
            List of extracted verification codes
        """
        codes = []
        message_lower = message_content.lower()

        # Try service-specific patterns first if service is provided
        if service_name and service_name.lower() in cls.SERVICE_PATTERNS:
            for pattern in cls.SERVICE_PATTERNS[service_name.lower()]:
                matches = re.findall(pattern, message_content, re.IGNORECASE)
                codes.extend(matches)

        # Try general patterns if no service-specific codes found
        if not codes:
            for pattern in cls.CODE_PATTERNS:
                matches = re.findall(pattern, message_content, re.IGNORECASE)
                codes.extend(matches)

        # Remove duplicates and filter valid codes
        unique_codes = []
        for code in codes:
            if code not in unique_codes and cls._is_valid_code(code):
                unique_codes.append(code)

        return unique_codes

    @classmethod
    def _is_valid_code(cls, code: str) -> bool:
        """Validate if extracted code looks like a verification code"""
        if not code or not code.isdigit():
            return False

        # Most verification codes are 4-8 digits
        if len(code) < 4 or len(code) > 8:
            return False

        # Avoid obvious non-codes like years, phone numbers, etc.
        if len(code) == 4 and code.startswith(("19", "20")):  # Years
            return False

        return True

    @classmethod
    def identify_service_patterns(
        cls, message_content: str, service_name: str
    ) -> Dict[str, Any]:
        """
        Identify service-specific patterns in message content

        Returns:
            Dictionary with pattern match information
        """
        result = {
            "service_detected": False,
            "confidence": 0.0,
            "patterns_matched": [],
            "extracted_codes": [],
        }

        message_lower = message_content.lower()
        service_lower = service_name.lower()

        # Check if service name appears in message
        if service_lower in message_lower:
            result["service_detected"] = True
            result["confidence"] += 0.5
            result["patterns_matched"].append(f"service_name_match: {service_name}")

        # Check service-specific patterns
        if service_lower in cls.SERVICE_PATTERNS:
            for pattern in cls.SERVICE_PATTERNS[service_lower]:
                matches = re.findall(pattern, message_content, re.IGNORECASE)
                if matches:
                    result["confidence"] += 0.3
                    result["patterns_matched"].append(f"pattern_match: {pattern}")
                    result["extracted_codes"].extend(matches)

        # Extract codes using general patterns
        general_codes = cls.extract_verification_codes(message_content)
        result["extracted_codes"].extend(general_codes)

        # Remove duplicates
        result["extracted_codes"] = list(set(result["extracted_codes"]))

        return result

    @classmethod
    def extract_verification_codes_with_confidence(
        cls, message_content: str, service_name: str = None
    ) -> Dict[str, float]:
        """
        Extract verification codes from SMS message content with confidence scores

        Args:
            message_content: The SMS message content
            service_name: Optional service name for service-specific patterns

        Returns:
            Dictionary mapping codes to confidence scores (0.0 to 1.0)
        """
        codes_with_confidence = {}
        message_lower = message_content.lower()

        # Try service-specific patterns first if service is provided
        if service_name and service_name.lower() in cls.SERVICE_PATTERNS:
            for pattern in cls.SERVICE_PATTERNS[service_name.lower()]:
                matches = re.findall(pattern, message_content, re.IGNORECASE)
                for match in matches:
                    codes_with_confidence[match] = 0.9  # High confidence for service-specific

        # Try general patterns
        if not codes_with_confidence:
            for pattern in cls.CODE_PATTERNS:
                matches = re.findall(pattern, message_content, re.IGNORECASE)
                for match in matches:
                    # Calculate confidence based on pattern specificity
                    confidence = cls._calculate_pattern_confidence(pattern, match, message_content)
                    codes_with_confidence[match] = confidence

        # Filter and validate codes
        validated_codes = {}
        for code, confidence in codes_with_confidence.items():
            if cls._is_valid_code(code):
                validated_codes[code] = confidence

        return validated_codes

    @classmethod
    def _calculate_pattern_confidence(cls, pattern: str, code: str, message: str) -> float:
        """Calculate confidence score for a pattern match"""
        base_confidence = 0.5

        # Increase confidence for longer codes
        if len(code) >= 6:
            base_confidence += 0.2

        # Increase confidence if code appears with verification keywords
        verification_keywords = ['code', 'verification', 'confirm', 'verify', 'otp', 'pin']
        message_lower = message.lower()
        if any(keyword in message_lower for keyword in verification_keywords):
            base_confidence += 0.2

        # Increase confidence for service-specific patterns
        if 'service' in pattern.lower():
            base_confidence += 0.1

        return min(base_confidence, 1.0)


class VerificationService:
    """Enhanced verification service with user association and tracking"""

    def __init__(
        self, db_session: Session, textverified_client: TextVerifiedClient = None
    ):
        self.db = db_session
        self.textverified_client = textverified_client
        self.code_extractor = CodeExtractionService()
        self.notification_service = NotificationService()

    @with_error_handling("verification_service", "create_verification")
    @textverified_retry_decorator(max_attempts=3, base_delay=1, max_delay=10)
    async def create_verification(
        self, user_id: str, service_name: str, capability: str = "sms"
    ) -> VerificationRequest:
        """
        Create a new verification request associated with a user

        Args:
            user_id: ID of the user creating the verification
            service_name: Name of the service to verify (e.g., 'whatsapp', 'google')
            capability: Verification capability ('sms', 'voice', 'smsAndVoiceCombo')

        Returns:
            VerificationRequest object
        """
        try:
            # Verify user exists and is active
            user = (
                self.db.query(User)
                .filter(and_(User.id == user_id, User.is_active == True))
                .first()
            )

            if not user:
                raise ValueError(f"User {user_id} not found or inactive")

            # Check user's verification limits
            await self._check_verification_limits(user)

            # Create verification with TextVerified
            if not self.textverified_client:
                raise ValueError("TextVerified client not configured")

            textverified_id = await self.textverified_client.create_verification(
                service_name=service_name, capability=capability
            )

            # Create database record
            verification = VerificationRequest(
                user_id=user_id,
                textverified_id=textverified_id,
                service_name=service_name,
                status="pending",
                expires_at=datetime.utcnow() + timedelta(minutes=30),
            )

            self.db.add(verification)
            self.db.commit()
            self.db.refresh(verification)

            # Start monitoring for this verification
            asyncio.create_task(self._monitor_verification(verification.id))

            logger.info(
                f"Created verification {verification.id} for user {user_id}, service {service_name}"
            )

            return verification

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create verification for user {user_id}: {e}")
            raise

    @with_error_handling("verification_service", "get_verification_number")
    @textverified_retry_decorator(max_attempts=3, base_delay=0.5, max_delay=5)
    async def get_verification_number(self, user_id: str, verification_id: str) -> str:
        """
        Get the phone number for a verification request

        Args:
            user_id: ID of the user
            verification_id: ID of the verification request

        Returns:
            Phone number string
        """
        try:
            verification = await self._get_user_verification(user_id, verification_id)

            if not verification.phone_number:
                # Get number from TextVerified
                phone_number = await self.textverified_client.get_verification_number(
                    verification.textverified_id
                )

                # Update database
                verification.phone_number = phone_number
                self.db.commit()

                logger.info(
                    f"Retrieved phone number {phone_number} for verification {verification_id}"
                )

            return verification.phone_number

        except Exception as e:
            logger.error(f"Failed to get verification number: {e}")
            raise

    @with_error_handling("verification_service", "check_verification_messages")
    @textverified_retry_decorator(max_attempts=5, base_delay=2, max_delay=15)
    async def check_verification_messages(
        self, user_id: str, verification_id: str
    ) -> List[str]:
        """
        Check for SMS messages and extract verification codes

        Args:
            user_id: ID of the user
            verification_id: ID of the verification request

        Returns:
            List of SMS messages received
        """
        try:
            verification = await self._get_user_verification(user_id, verification_id)

            # Get messages from TextVerified
            messages = await self.textverified_client.get_sms_messages(
                verification.textverified_id
            )

            if messages:
                # Extract verification codes from messages
                all_codes = []
                for message in messages:
                    codes = self.code_extractor.extract_verification_codes(
                        message, verification.service_name
                    )
                    all_codes.extend(codes)

                # Update verification if we found codes
                if all_codes and not verification.verification_code:
                    verification.verification_code = all_codes[
                        0
                    ]  # Use first code found
                    verification.status = "completed"
                    verification.completed_at = datetime.utcnow()
                    self.db.commit()

                    # Send notification to user
                    await self.notification_service.send_verification_completed(
                        user_id,
                        verification.service_name,
                        verification.verification_code,
                    )

                    logger.info(
                        f"Verification {verification_id} completed with code {verification.verification_code}"
                    )

            return messages

        except Exception as e:
            logger.error(f"Failed to check verification messages: {e}")
            raise

    async def get_verification_history(
        self, user_id: str, filters: Dict[str, Any] = None
    ) -> List[VerificationRequest]:
        """
        Get verification history for a user with optional filters

        Args:
            user_id: ID of the user
            filters: Optional filters (service_name, status, date_range, etc.)

        Returns:
            List of VerificationRequest objects
        """
        try:
            query = self.db.query(VerificationRequest).filter(
                VerificationRequest.user_id == user_id
            )

            # Apply filters
            if filters:
                if "service_name" in filters:
                    query = query.filter(
                        VerificationRequest.service_name.ilike(
                            f"%{filters['service_name']}%"
                        )
                    )

                if "status" in filters:
                    query = query.filter(
                        VerificationRequest.status == filters["status"]
                    )

                if "date_from" in filters:
                    query = query.filter(
                        VerificationRequest.created_at >= filters["date_from"]
                    )

                if "date_to" in filters:
                    query = query.filter(
                        VerificationRequest.created_at <= filters["date_to"]
                    )

            # Order by creation date (newest first)
            verifications = query.order_by(desc(VerificationRequest.created_at)).all()

            logger.info(
                f"Retrieved {len(verifications)} verification records for user {user_id}"
            )

            return verifications

        except Exception as e:
            logger.error(f"Failed to get verification history: {e}")
            raise

    async def search_verifications(
        self, user_id: str, search_query: str, filters: Dict[str, Any] = None
    ) -> List[VerificationRequest]:
        """
        Search verification history with text query

        Args:
            user_id: ID of the user
            search_query: Text to search for
            filters: Optional additional filters

        Returns:
            List of matching VerificationRequest objects
        """
        try:
            query = self.db.query(VerificationRequest).filter(
                VerificationRequest.user_id == user_id
            )

            # Add text search
            if search_query:
                search_filter = or_(
                    VerificationRequest.service_name.ilike(f"%{search_query}%"),
                    VerificationRequest.phone_number.ilike(f"%{search_query}%"),
                    VerificationRequest.verification_code.ilike(f"%{search_query}%"),
                )
                query = query.filter(search_filter)

            # Apply additional filters
            if filters:
                if "status" in filters:
                    query = query.filter(
                        VerificationRequest.status == filters["status"]
                    )

                if "date_from" in filters:
                    query = query.filter(
                        VerificationRequest.created_at >= filters["date_from"]
                    )

                if "date_to" in filters:
                    query = query.filter(
                        VerificationRequest.created_at <= filters["date_to"]
                    )

            results = query.order_by(desc(VerificationRequest.created_at)).all()

            logger.info(
                f"Search '{search_query}' returned {len(results)} results for user {user_id}"
            )

            return results

        except Exception as e:
            logger.error(f"Failed to search verifications: {e}")
            raise

    @with_error_handling("verification_service", "cancel_verification")
    @textverified_retry_decorator(max_attempts=2, base_delay=1, max_delay=5)
    async def cancel_verification(self, user_id: str, verification_id: str) -> bool:
        """
        Cancel a verification request

        Args:
            user_id: ID of the user
            verification_id: ID of the verification to cancel

        Returns:
            True if successful
        """
        try:
            verification = await self._get_user_verification(user_id, verification_id)

            if verification.status in ["completed", "cancelled", "expired"]:
                raise ValueError(
                    f"Cannot cancel verification with status: {verification.status}"
                )

            # Cancel with TextVerified
            await self.textverified_client.cancel_verification(
                verification.textverified_id
            )

            # Update database
            verification.status = "cancelled"
            self.db.commit()

            logger.info(f"Cancelled verification {verification_id} for user {user_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to cancel verification: {e}")
            raise

    async def get_verification_statistics(
        self, user_id: str, period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get enhanced verification statistics for a user

        Args:
            user_id: ID of the user
            period_days: Number of days to include in statistics

        Returns:
            Dictionary with enhanced statistics including completion times and costs
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=period_days)

            # Get verification counts by status
            status_counts = (
                self.db.query(
                    VerificationRequest.status,
                    func.count(VerificationRequest.id).label("count"),
                )
                .filter(
                    and_(
                        VerificationRequest.user_id == user_id,
                        VerificationRequest.created_at >= since_date,
                    )
                )
                .group_by(VerificationRequest.status)
                .all()
            )

            # Get service usage
            service_counts = (
                self.db.query(
                    VerificationRequest.service_name,
                    func.count(VerificationRequest.id).label("count"),
                )
                .filter(
                    and_(
                        VerificationRequest.user_id == user_id,
                        VerificationRequest.created_at >= since_date,
                    )
                )
                .group_by(VerificationRequest.service_name)
                .all()
            )

            # Calculate completion times for completed verifications
            completed_verifications = (
                self.db.query(VerificationRequest)
                .filter(
                    and_(
                        VerificationRequest.user_id == user_id,
                        VerificationRequest.created_at >= since_date,
                        VerificationRequest.status == "completed",
                        VerificationRequest.completed_at.isnot(None),
                    )
                )
                .all()
            )

            completion_times = []
            for verification in completed_verifications:
                if verification.completed_at and verification.created_at:
                    time_diff = (verification.completed_at - verification.created_at).total_seconds() / 60  # minutes
                    completion_times.append(time_diff)

            average_completion_time = (
                sum(completion_times) / len(completion_times) if completion_times else None
            )

            # Calculate success rate
            total_verifications = sum(count for _, count in status_counts)
            completed_count = next(
                (count for status, count in status_counts if status == "completed"), 0
            )
            success_rate = (
                (completed_count / total_verifications * 100)
                if total_verifications > 0
                else 0
            )

            # Mock cost calculation (would be integrated with real pricing)
            total_cost = total_verifications * 0.15  # Average cost per verification
            cost_by_service = {service: count * 0.15 for service, count in service_counts}

            statistics = {
                "period_days": period_days,
                "total_verifications": total_verifications,
                "completed_verifications": completed_count,
                "success_rate": round(success_rate, 2),
                "average_completion_time": round(average_completion_time, 2) if average_completion_time else None,
                "total_cost": round(total_cost, 2),
                "status_breakdown": {status: count for status, count in status_counts},
                "service_usage": {service: count for service, count in service_counts},
                "cost_by_service": {service: round(cost, 2) for service, cost in cost_by_service.items()},
                "generated_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Generated enhanced verification statistics for user {user_id}")

            return statistics

        except Exception as e:
            logger.error(f"Failed to get verification statistics: {e}")
            raise

    async def export_verification_data(
        self, user_id: str, format_type: str = "json", filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Export verification data for a user

        Args:
            user_id: ID of the user
            format_type: Export format ('json', 'csv')
            filters: Optional filters to apply

        Returns:
            Dictionary with export data and metadata
        """
        try:
            verifications = await self.get_verification_history(user_id, filters)

            export_data = []
            for verification in verifications:
                record = {
                    "id": verification.id,
                    "service_name": verification.service_name,
                    "phone_number": verification.phone_number,
                    "status": verification.status,
                    "verification_code": verification.verification_code,
                    "created_at": (
                        verification.created_at.isoformat()
                        if verification.created_at
                        else None
                    ),
                    "completed_at": (
                        verification.completed_at.isoformat()
                        if verification.completed_at
                        else None
                    ),
                    "expires_at": (
                        verification.expires_at.isoformat()
                        if verification.expires_at
                        else None
                    ),
                }
                export_data.append(record)

            result = {
                "format": format_type,
                "user_id": user_id,
                "record_count": len(export_data),
                "exported_at": datetime.utcnow().isoformat(),
                "data": export_data,
            }

            if format_type == "csv":
                # Convert to CSV format
                import csv
                import io

                output = io.StringIO()
                if export_data:
                    writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                    writer.writeheader()
                    writer.writerows(export_data)

                result["csv_content"] = output.getvalue()
                output.close()

            logger.info(
                f"Exported {len(export_data)} verification records for user {user_id} in {format_type} format"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to export verification data: {e}")
            raise

    async def _get_user_verification(
        self, user_id: str, verification_id: str
    ) -> VerificationRequest:
        """Get verification request ensuring it belongs to the user"""
        verification = (
            self.db.query(VerificationRequest)
            .filter(
                and_(
                    VerificationRequest.id == verification_id,
                    VerificationRequest.user_id == user_id,
                )
            )
            .first()
        )

        if not verification:
            raise ValueError(
                f"Verification {verification_id} not found for user {user_id}"
            )

        return verification

    async def _check_verification_limits(self, user: User):
        """Check if user can create new verification requests"""
        # Check daily limits based on subscription
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        daily_count = (
            self.db.query(VerificationRequest)
            .filter(
                and_(
                    VerificationRequest.user_id == user.id,
                    VerificationRequest.created_at >= today_start,
                )
            )
            .count()
        )

        # Define limits based on subscription plan
        limits = {"free": 5, "basic": 20, "premium": 100, "enterprise": 500}

        user_limit = limits.get(user.subscription_plan, 5)

        if daily_count >= user_limit:
            raise ValueError(
                f"Daily verification limit ({user_limit}) reached for subscription plan: {user.subscription_plan}"
            )

    async def _monitor_verification(self, verification_id: str):
        """
        Background task to monitor verification status and auto-extract codes
        """
        try:
            max_attempts = 30  # Monitor for 15 minutes (30 * 30 seconds)
            attempt = 0

            while attempt < max_attempts:
                await asyncio.sleep(30)  # Check every 30 seconds
                attempt += 1

                verification = (
                    self.db.query(VerificationRequest)
                    .filter(VerificationRequest.id == verification_id)
                    .first()
                )

                if not verification or verification.status in [
                    "completed",
                    "cancelled",
                    "expired",
                ]:
                    break

                # Check for messages
                try:
                    messages = await self.textverified_client.get_sms_messages(
                        verification.textverified_id
                    )

                    if messages and not verification.verification_code:
                        # Extract codes with confidence scoring
                        all_codes = []
                        for message in messages:
                            codes_with_confidence = self.code_extractor.extract_verification_codes_with_confidence(
                                message, verification.service_name
                            )
                            # Only use codes with high confidence (>0.7)
                            high_confidence_codes = [code for code, conf in codes_with_confidence.items() if conf > 0.7]
                            all_codes.extend(high_confidence_codes)

                        if all_codes:
                            verification.verification_code = all_codes[0]
                            verification.status = "completed"
                            verification.completed_at = datetime.utcnow()
                            self.db.commit()

                            # Send notification
                            await self.notification_service.send_verification_completed(
                                verification.user_id,
                                verification.service_name,
                                verification.verification_code,
                            )

                            logger.info(
                                f"Auto-completed verification {verification_id} with code {verification.verification_code}"
                            )
                            break

                except Exception as e:
                    logger.warning(
                        f"Error monitoring verification {verification_id}: {e}"
                    )

            # Mark as expired if not completed
            if attempt >= max_attempts:
                verification = (
                    self.db.query(VerificationRequest)
                    .filter(VerificationRequest.id == verification_id)
                    .first()
                )

                if verification and verification.status == "pending":
                    verification.status = "expired"
                    self.db.commit()

                    logger.info(
                        f"Verification {verification_id} expired after monitoring timeout"
                    )

        except Exception as e:
            logger.error(f"Error in verification monitoring task: {e}")
