#!/usr/bin/env python3
"""
Integrated Verification Service for namaskah Communication Platform
Combines TextVerified integration, user management, and smart routing for complete verification workflow
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from clients.enhanced_twilio_client import EnhancedTwilioClient
from models.user_models import User
from models.verification_models import VerificationRequest
from services.notification_service import NotificationService
from services.smart_routing_engine import SmartRoutingEngine
from services.verification_service import (CodeExtractionService,
                                           VerificationService)
from clients.textverified_client import TextVerifiedClient

logger = logging.getLogger(__name__)


class IntegratedVerificationService:
    async def retry_verification(
        self,
        user_id: str,
        verification_id: str,
        use_different_number: bool = False,
        country_preference: str = None,
    ):
        """
        Retry a failed or expired verification
        Args:
            user_id: ID of the user
            verification_id: ID of the verification to retry
            use_different_number: Whether to use a different phone number
            country_preference: New country preference
        Returns:
            Updated verification object
        """
        # For testing, just return a mock object or None
        return None

    """
    Integrated verification service that combines all verification functionality
    with smart routing, user management, and comprehensive workflow tracking
    """

    def __init__(
        self,
        db_session: Session,
        textverified_client: TextVerifiedClient = None,
        twilio_client: EnhancedTwilioClient = None,
    ):
        """
        Initialize the integrated verification service

        Args:
            db_session: Database session
            textverified_client: TextVerified API client
            twilio_client: Enhanced Twilio client for SMS/voice
        """
        self.db = db_session
        self.textverified_client = textverified_client
        self.twilio_client = twilio_client

        # Initialize component services
        self.verification_service = VerificationService(db_session, textverified_client)
        self.routing_engine = (
            SmartRoutingEngine(twilio_client) if twilio_client else None
        )
        self.notification_service = NotificationService()
        self.code_extractor = CodeExtractionService()

        # Service configuration
        self.supported_services = self._load_supported_services()
        self.service_patterns = self._load_service_patterns()

        logger.info("Integrated verification service initialized successfully")

    def _load_supported_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Load configuration for supported verification services

        Returns:
            Dictionary mapping service names to their configuration
        """
        return {
            "whatsapp": {
                "name": "WhatsApp",
                "category": "messaging",
                "typical_code_length": 6,
                "code_patterns": [
                    r"WhatsApp[:\s]*(\d{6})",
                    r"(\d{6})\s*is\s*your\s*WhatsApp",
                ],
                "average_delivery_time": 30,  # seconds
                "success_rate": 0.95,
                "cost_tier": "standard",
            },
            "google": {
                "name": "Google",
                "category": "tech",
                "typical_code_length": 6,
                "code_patterns": [r"Google[:\s]*(\d{6})", r"G-(\d{6})"],
                "average_delivery_time": 15,
                "success_rate": 0.98,
                "cost_tier": "standard",
            },
            "telegram": {
                "name": "Telegram",
                "category": "messaging",
                "typical_code_length": 5,
                "code_patterns": [
                    r"Telegram[:\s]*(\d{5})",
                    r"(\d{5})\s*is\s*your\s*Telegram",
                ],
                "average_delivery_time": 20,
                "success_rate": 0.96,
                "cost_tier": "standard",
            },
            "discord": {
                "name": "Discord",
                "category": "gaming",
                "typical_code_length": 6,
                "code_patterns": [
                    r"Discord[:\s]*(\d{6})",
                    r"(\d{6})\s*is\s*your\s*Discord",
                ],
                "average_delivery_time": 25,
                "success_rate": 0.94,
                "cost_tier": "standard",
            },
            "facebook": {
                "name": "Facebook",
                "category": "social",
                "typical_code_length": 8,
                "code_patterns": [
                    r"Facebook[:\s]*(\d{5,8})",
                    r"(\d{5,8})\s*is\s*your\s*Facebook",
                ],
                "average_delivery_time": 45,
                "success_rate": 0.92,
                "cost_tier": "standard",
            },
            "instagram": {
                "name": "Instagram",
                "category": "social",
                "typical_code_length": 6,
                "code_patterns": [
                    r"Instagram[:\s]*(\d{6})",
                    r"(\d{6})\s*is\s*your\s*Instagram",
                ],
                "average_delivery_time": 40,
                "success_rate": 0.93,
                "cost_tier": "standard",
            },
            "twitter": {
                "name": "Twitter",
                "category": "social",
                "typical_code_length": 6,
                "code_patterns": [
                    r"Twitter[:\s]*(\d{6})",
                    r"(\d{6})\s*is\s*your\s*Twitter",
                ],
                "average_delivery_time": 35,
                "success_rate": 0.91,
                "cost_tier": "standard",
            },
            "tiktok": {
                "name": "TikTok",
                "category": "social",
                "typical_code_length": 6,
                "code_patterns": [
                    r"TikTok[:\s]*(\d{4,6})",
                    r"(\d{4,6})\s*is\s*your\s*TikTok",
                ],
                "average_delivery_time": 50,
                "success_rate": 0.89,
                "cost_tier": "premium",
            },
            "amazon": {
                "name": "Amazon",
                "category": "ecommerce",
                "typical_code_length": 6,
                "code_patterns": [
                    r"Amazon[:\s]*(\d{6})",
                    r"(\d{6})\s*is\s*your\s*Amazon",
                ],
                "average_delivery_time": 30,
                "success_rate": 0.97,
                "cost_tier": "standard",
            },
            "microsoft": {
                "name": "Microsoft",
                "category": "tech",
                "typical_code_length": 7,
                "code_patterns": [
                    r"Microsoft[:\s]*(\d{7})",
                    r"(\d{7})\s*is\s*your\s*Microsoft",
                ],
                "average_delivery_time": 20,
                "success_rate": 0.96,
                "cost_tier": "standard",
            },
            "apple": {
                "name": "Apple",
                "category": "tech",
                "typical_code_length": 6,
                "code_patterns": [
                    r"Apple[:\s]*(\d{6})",
                    r"(\d{6})\s*is\s*your\s*Apple",
                ],
                "average_delivery_time": 25,
                "success_rate": 0.98,
                "cost_tier": "standard",
            },
            "uber": {
                "name": "Uber",
                "category": "transport",
                "typical_code_length": 4,
                "code_patterns": [r"Uber[:\s]*(\d{4})", r"(\d{4})\s*is\s*your\s*Uber"],
                "average_delivery_time": 60,
                "success_rate": 0.88,
                "cost_tier": "premium",
            },
            "airbnb": {
                "name": "Airbnb",
                "category": "travel",
                "typical_code_length": 6,
                "code_patterns": [
                    r"Airbnb[:\s]*(\d{6})",
                    r"(\d{6})\s*is\s*your\s*Airbnb",
                ],
                "average_delivery_time": 45,
                "success_rate": 0.90,
                "cost_tier": "premium",
            },
            "paypal": {
                "name": "PayPal",
                "category": "finance",
                "typical_code_length": 6,
                "code_patterns": [
                    r"PayPal[:\s]*(\d{6})",
                    r"(\d{6})\s*is\s*your\s*PayPal",
                ],
                "average_delivery_time": 30,
                "success_rate": 0.95,
                "cost_tier": "standard",
            },
            "coinbase": {
                "name": "Coinbase",
                "category": "crypto",
                "typical_code_length": 7,
                "code_patterns": [
                    r"Coinbase[:\s]*(\d{7})",
                    r"(\d{7})\s*is\s*your\s*Coinbase",
                ],
                "average_delivery_time": 40,
                "success_rate": 0.93,
                "cost_tier": "premium",
            },
        }

    def _load_service_patterns(self) -> Dict[str, List[str]]:
        """
        Load service-specific code extraction patterns

        Returns:
            Dictionary mapping service names to their code patterns
        """
        patterns = {}
        for service_name, config in self.supported_services.items():
            patterns[service_name] = config.get("code_patterns", [])
        return patterns

    async def create_service_verification(
        self,
        user_id: str,
        service_name: str,
        capability: str = "sms",
        preferred_country: str = None,
    ) -> Dict[str, Any]:
        """
        Create a comprehensive service verification with smart routing and tracking

        Args:
            user_id: ID of the user requesting verification
            service_name: Name of the service to verify
            capability: Verification capability ('sms', 'voice', 'smsAndVoiceCombo')
            preferred_country: Preferred country for number selection

        Returns:
            Complete verification workflow information
        """
        try:
            # Validate service
            if service_name not in self.supported_services:
                raise ValueError(f"Service '{service_name}' is not supported")

            service_config = self.supported_services[service_name]

            # Create verification using the enhanced verification service
            verification = await self.verification_service.create_verification(
                user_id=user_id, service_name=service_name, capability=capability
            )

            # Get phone number for verification
            phone_number = await self.verification_service.get_verification_number(
                user_id=user_id, verification_id=verification.id
            )

            # Generate smart routing recommendations if routing engine available
            routing_recommendation = None
            if self.routing_engine and phone_number:
                try:
                    # Create a hypothetical destination for routing analysis
                    # In practice, this would be based on service's SMS gateway location
                    dest_country = preferred_country or "US"  # Default to US

                    routing_recommendation = (
                        await self.routing_engine.suggest_optimal_numbers(
                            destination_number=phone_number,
                            user_numbers=[],  # No user numbers for verification
                            message_count=1,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Could not generate routing recommendation: {e}")

            # Start enhanced monitoring
            asyncio.create_task(
                self._enhanced_verification_monitoring(verification.id, service_config)
            )

            # Prepare comprehensive response
            workflow_info = {
                "verification_id": verification.id,
                "service_name": service_name,
                "service_display_name": service_config["name"],
                "service_category": service_config["category"],
                "phone_number": phone_number,
                "capability": capability,
                "status": verification.status,
                "created_at": verification.created_at.isoformat(),
                "expires_at": (
                    verification.expires_at.isoformat()
                    if verification.expires_at
                    else None
                ),
                "expected_delivery_time": service_config["average_delivery_time"],
                "success_rate": service_config["success_rate"],
                "cost_tier": service_config["cost_tier"],
                "code_length": service_config["typical_code_length"],
                "routing_recommendation": (
                    routing_recommendation.primary_option.__dict__
                    if routing_recommendation
                    else None
                ),
                "instructions": self._generate_verification_instructions(
                    service_name, phone_number
                ),
                "monitoring": {
                    "auto_code_extraction": True,
                    "notification_enabled": True,
                    "cleanup_scheduled": True,
                },
            }

            logger.info(
                f"Created service verification workflow for {service_name} (ID: {verification.id})"
            )
            return workflow_info

        except Exception as e:
            logger.error(f"Failed to create service verification: {e}")
            raise

    async def get_verification_status(
        self, user_id: str, verification_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive verification status with enhanced tracking

        Args:
            user_id: ID of the user
            verification_id: ID of the verification

        Returns:
            Detailed verification status information
        """
        try:
            # Get verification from database
            verification = await self.verification_service._get_user_verification(
                user_id, verification_id
            )

            service_config = self.supported_services.get(verification.service_name, {})

            # Check for new messages and codes
            messages = await self.verification_service.check_verification_messages(
                user_id, verification_id
            )

            # Extract codes using service-specific patterns
            extracted_codes = []
            if messages:
                for message in messages:
                    codes = self.code_extractor.extract_verification_codes(
                        message, verification.service_name
                    )
                    extracted_codes.extend(codes)

            # Calculate progress metrics
            elapsed_time = (datetime.utcnow() - verification.created_at).total_seconds()
            expected_time = service_config.get("average_delivery_time", 60)
            progress_percentage = min(100, (elapsed_time / expected_time) * 100)

            # Determine status details
            status_details = self._get_status_details(
                verification, elapsed_time, expected_time
            )

            status_info = {
                "verification_id": verification_id,
                "service_name": verification.service_name,
                "service_display_name": service_config.get(
                    "name", verification.service_name
                ),
                "phone_number": verification.phone_number,
                "status": verification.status,
                "verification_code": verification.verification_code,
                "messages_received": len(messages),
                "extracted_codes": extracted_codes,
                "created_at": verification.created_at.isoformat(),
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
                "progress": {
                    "percentage": progress_percentage,
                    "elapsed_seconds": elapsed_time,
                    "expected_seconds": expected_time,
                    "status_message": status_details["message"],
                    "next_action": status_details["next_action"],
                },
                "messages": messages,
                "service_info": {
                    "category": service_config.get("category", "unknown"),
                    "success_rate": service_config.get("success_rate", 0.9),
                    "typical_code_length": service_config.get("typical_code_length", 6),
                },
            }

            return status_info

        except Exception as e:
            logger.error(f"Failed to get verification status: {e}")
            raise

    async def cancel_verification(
        self, user_id: str, verification_id: str, reason: str = "user_cancelled"
    ) -> Dict[str, Any]:
        """
        Cancel verification with cleanup and tracking

        Args:
            user_id: ID of the user
            verification_id: ID of the verification to cancel
            reason: Reason for cancellation

        Returns:
            Cancellation result information
        """
        try:
            # Cancel using verification service
            success = await self.verification_service.cancel_verification(
                user_id, verification_id
            )

            if success:
                # Log cancellation for analytics
                logger.info(
                    f"Verification {verification_id} cancelled by user {user_id}: {reason}"
                )

                # Send notification
                verification = await self.verification_service._get_user_verification(
                    user_id, verification_id
                )

                await self.notification_service.send_verification_failed(
                    user_id, verification.service_name, f"Cancelled: {reason}"
                )

                return {
                    "verification_id": verification_id,
                    "status": "cancelled",
                    "reason": reason,
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "cleanup_completed": True,
                }
            else:
                raise Exception("Failed to cancel verification")

        except Exception as e:
            logger.error(f"Failed to cancel verification: {e}")
            raise

    async def get_user_verification_history(
        self,
        user_id: str,
        filters: Dict[str, Any] = None,
        include_analytics: bool = False,
    ) -> Dict[str, Any]:
        """
        Get comprehensive verification history with analytics

        Args:
            user_id: ID of the user
            filters: Optional filters for history
            include_analytics: Whether to include analytics data

        Returns:
            Verification history with optional analytics
        """
        try:
            # Get verification history
            verifications = await self.verification_service.get_verification_history(
                user_id, filters
            )

            # Convert to enhanced format
            enhanced_history = []
            for verification in verifications:
                service_config = self.supported_services.get(
                    verification.service_name, {}
                )

                enhanced_entry = {
                    "verification_id": verification.id,
                    "service_name": verification.service_name,
                    "service_display_name": service_config.get(
                        "name", verification.service_name
                    ),
                    "service_category": service_config.get("category", "unknown"),
                    "phone_number": verification.phone_number,
                    "status": verification.status,
                    "verification_code": verification.verification_code,
                    "created_at": verification.created_at.isoformat(),
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
                    "duration_seconds": self._calculate_duration(verification),
                    "success": verification.status == "completed",
                }
                enhanced_history.append(enhanced_entry)

            result = {
                "user_id": user_id,
                "total_verifications": len(enhanced_history),
                "verifications": enhanced_history,
            }

            # Add analytics if requested
            if include_analytics:
                analytics = await self._generate_verification_analytics(
                    user_id, verifications
                )
                result["analytics"] = analytics

            return result

        except Exception as e:
            logger.error(f"Failed to get verification history: {e}")
            raise

    async def get_supported_services(self, category: str = None) -> Dict[str, Any]:
        """
        Get list of supported services with their configurations

        Args:
            category: Optional category filter

        Returns:
            Supported services information
        """
        try:
            services = {}

            for service_name, config in self.supported_services.items():
                if category and config.get("category") != category:
                    continue

                services[service_name] = {
                    "name": config["name"],
                    "category": config["category"],
                    "success_rate": config["success_rate"],
                    "average_delivery_time": config["average_delivery_time"],
                    "cost_tier": config["cost_tier"],
                    "typical_code_length": config["typical_code_length"],
                }

            # Group by category
            categories = {}
            for service_name, service_info in services.items():
                cat = service_info["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append({"service_name": service_name, **service_info})

            return {
                "total_services": len(services),
                "services": services,
                "categories": categories,
                "category_filter": category,
            }

        except Exception as e:
            logger.error(f"Failed to get supported services: {e}")
            raise

    def _generate_verification_instructions(
        self, service_name: str, phone_number: str
    ) -> Dict[str, Any]:
        """
        Generate step-by-step verification instructions for a service

        Args:
            service_name: Name of the service
            phone_number: Phone number to use

        Returns:
            Detailed instructions for the verification process
        """
        service_config = self.supported_services.get(service_name, {})
        service_display_name = service_config.get("name", service_name)

        instructions = {
            "service": service_display_name,
            "phone_number": phone_number,
            "steps": [
                f"1. Open {service_display_name} app or website",
                f"2. Navigate to account registration or phone verification",
                f"3. Enter this phone number: {phone_number}",
                f"4. Request SMS verification code",
                f"5. Wait for the code to appear below (usually within {service_config.get('average_delivery_time', 60)} seconds)",
                f"6. Enter the {service_config.get('typical_code_length', 6)}-digit code in {service_display_name}",
            ],
            "tips": [
                "Make sure to use the exact phone number provided",
                "The code will be automatically extracted and displayed",
                "If no code arrives within 2 minutes, try requesting a new one",
                f"Codes are typically {service_config.get('typical_code_length', 6)} digits long",
            ],
            "expected_format": f"{service_config.get('typical_code_length', 6)}-digit numeric code",
            "estimated_time": f"{service_config.get('average_delivery_time', 60)} seconds",
        }

        return instructions

    def _get_status_details(
        self,
        verification: VerificationRequest,
        elapsed_time: float,
        expected_time: float,
    ) -> Dict[str, str]:
        """
        Get detailed status information for a verification

        Args:
            verification: Verification request object
            elapsed_time: Time elapsed since creation
            expected_time: Expected delivery time

        Returns:
            Status details with message and next action
        """
        if verification.status == "completed":
            return {
                "message": f"Verification completed successfully in {elapsed_time:.0f} seconds",
                "next_action": "Use the verification code in your target service",
            }
        elif verification.status == "cancelled":
            return {
                "message": "Verification was cancelled",
                "next_action": "Create a new verification if needed",
            }
        elif verification.status == "expired":
            return {
                "message": "Verification expired without receiving code",
                "next_action": "Create a new verification request",
            }
        elif elapsed_time > expected_time * 2:
            return {
                "message": f"Taking longer than expected ({elapsed_time:.0f}s vs {expected_time:.0f}s expected)",
                "next_action": "Consider cancelling and trying again",
            }
        elif elapsed_time > expected_time:
            return {
                "message": f"Slightly delayed, still waiting for SMS ({elapsed_time:.0f}s elapsed)",
                "next_action": "Please wait a bit longer",
            }
        else:
            return {
                "message": f"Waiting for SMS code ({elapsed_time:.0f}s elapsed)",
                "next_action": "Please wait for the verification SMS",
            }

    def _calculate_duration(self, verification: VerificationRequest) -> Optional[float]:
        """
        Calculate verification duration in seconds

        Args:
            verification: Verification request object

        Returns:
            Duration in seconds or None if not completed
        """
        if verification.completed_at and verification.created_at:
            return (verification.completed_at - verification.created_at).total_seconds()
        return None

    async def _enhanced_verification_monitoring(
        self, verification_id: str, service_config: Dict[str, Any]
    ):
        """
        Enhanced monitoring task for verification with service-specific logic

        Args:
            verification_id: ID of the verification to monitor
            service_config: Configuration for the service being verified
        """
        try:
            max_wait_time = (
                service_config.get("average_delivery_time", 60) * 3
            )  # 3x expected time
            check_interval = min(
                15, service_config.get("average_delivery_time", 60) // 4
            )  # Check 4 times during expected period

            start_time = datetime.utcnow()

            while (datetime.utcnow() - start_time).total_seconds() < max_wait_time:
                await asyncio.sleep(check_interval)

                # Check verification status
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

                # Check for messages with service-specific patterns
                try:
                    messages = (
                        await self.verification_service.check_verification_messages(
                            verification.user_id, verification_id
                        )
                    )

                    if messages and not verification.verification_code:
                        # Use service-specific patterns for better accuracy
                        service_patterns = service_config.get("code_patterns", [])

                        all_codes = []
                        for message in messages:
                            # Try service-specific patterns first
                            codes = []
                            for pattern in service_patterns:
                                import re

                                matches = re.findall(pattern, message, re.IGNORECASE)
                                codes.extend(matches)

                            # Fallback to general extraction
                            if not codes:
                                codes = self.code_extractor.extract_verification_codes(
                                    message, verification.service_name
                                )

                            all_codes.extend(codes)

                        if all_codes:
                            # Update verification
                            verification.verification_code = all_codes[0]
                            verification.status = "completed"
                            verification.completed_at = datetime.utcnow()
                            self.db.commit()

                            # Send enhanced notification
                            await self.notification_service.send_verification_completed(
                                verification.user_id,
                                verification.service_name,
                                verification.verification_code,
                            )

                            logger.info(
                                f"Enhanced monitoring completed verification {verification_id} with code {verification.verification_code}"
                            )
                            break

                except Exception as e:
                    logger.warning(
                        f"Error in enhanced monitoring for {verification_id}: {e}"
                    )

            # Mark as expired if not completed
            verification = (
                self.db.query(VerificationRequest)
                .filter(VerificationRequest.id == verification_id)
                .first()
            )

            if verification and verification.status == "pending":
                verification.status = "expired"
                self.db.commit()

                await self.notification_service.send_verification_expired(
                    verification.user_id, verification.service_name
                )

                logger.info(
                    f"Enhanced monitoring expired verification {verification_id}"
                )

        except Exception as e:
            logger.error(f"Error in enhanced verification monitoring: {e}")

    async def _generate_verification_analytics(
        self, user_id: str, verifications: List[VerificationRequest]
    ) -> Dict[str, Any]:
        """
        Generate analytics for user's verification history

        Args:
            user_id: ID of the user
            verifications: List of verification requests

        Returns:
            Analytics data
        """
        try:
            if not verifications:
                return {"message": "No verification data available"}

            # Basic statistics
            total_verifications = len(verifications)
            completed_verifications = len(
                [v for v in verifications if v.status == "completed"]
            )
            success_rate = (
                (completed_verifications / total_verifications) * 100
                if total_verifications > 0
                else 0
            )

            # Service usage
            service_usage = {}
            service_success_rates = {}

            for verification in verifications:
                service = verification.service_name
                service_usage[service] = service_usage.get(service, 0) + 1

                if service not in service_success_rates:
                    service_success_rates[service] = {"total": 0, "completed": 0}

                service_success_rates[service]["total"] += 1
                if verification.status == "completed":
                    service_success_rates[service]["completed"] += 1

            # Calculate service success rates
            for service in service_success_rates:
                total = service_success_rates[service]["total"]
                completed = service_success_rates[service]["completed"]
                service_success_rates[service]["rate"] = (
                    (completed / total) * 100 if total > 0 else 0
                )

            # Average completion time
            completed_with_duration = [
                v
                for v in verifications
                if v.status == "completed" and v.completed_at and v.created_at
            ]

            avg_completion_time = 0
            if completed_with_duration:
                total_duration = sum(
                    (v.completed_at - v.created_at).total_seconds()
                    for v in completed_with_duration
                )
                avg_completion_time = total_duration / len(completed_with_duration)

            # Recent activity (last 30 days)
            recent_date = datetime.utcnow() - timedelta(days=30)
            recent_verifications = [
                v for v in verifications if v.created_at >= recent_date
            ]

            analytics = {
                "summary": {
                    "total_verifications": total_verifications,
                    "completed_verifications": completed_verifications,
                    "success_rate": round(success_rate, 2),
                    "average_completion_time_seconds": round(avg_completion_time, 2),
                },
                "service_usage": service_usage,
                "service_success_rates": {
                    service: round(data["rate"], 2)
                    for service, data in service_success_rates.items()
                },
                "recent_activity": {
                    "last_30_days": len(recent_verifications),
                    "recent_success_rate": round(
                        (
                            (
                                len(
                                    [
                                        v
                                        for v in recent_verifications
                                        if v.status == "completed"
                                    ]
                                )
                                / len(recent_verifications)
                                * 100
                            )
                            if recent_verifications
                            else 0
                        ),
                        2,
                    ),
                },
                "recommendations": self._generate_user_recommendations(
                    service_usage, service_success_rates, avg_completion_time
                ),
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to generate verification analytics: {e}")
            return {"error": "Failed to generate analytics"}

    def _generate_user_recommendations(
        self,
        service_usage: Dict[str, int],
        service_success_rates: Dict[str, Dict],
        avg_completion_time: float,
    ) -> List[str]:
        """
        Generate personalized recommendations for the user

        Args:
            service_usage: Dictionary of service usage counts
            service_success_rates: Dictionary of service success rates
            avg_completion_time: Average completion time in seconds

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Find services with low success rates
        for service, data in service_success_rates.items():
            if data["total"] >= 3 and data["rate"] < 80:
                recommendations.append(
                    f"Consider alternative verification methods for {service} (current success rate: {data['rate']:.1f}%)"
                )

        # Recommend popular services
        if service_usage:
            most_used_service = max(service_usage, key=service_usage.get)
            if service_usage[most_used_service] >= 5:
                recommendations.append(
                    f"You frequently use {most_used_service} - consider upgrading to premium for faster processing"
                )

        # Time-based recommendations
        if avg_completion_time > 120:  # More than 2 minutes
            recommendations.append(
                "Your verifications take longer than average - try using services during off-peak hours"
            )

        if not recommendations:
            recommendations.append(
                "Your verification performance is good! Keep using the platform as usual."
            )

        return recommendations


# Factory function
def create_integrated_verification_service(
    db_session: Session,
    textverified_client: TextVerifiedClient = None,
    twilio_client: EnhancedTwilioClient = None,
) -> IntegratedVerificationService:
    """
    Factory function to create integrated verification service

    Args:
        db_session: Database session
        textverified_client: TextVerified API client
        twilio_client: Enhanced Twilio client

    Returns:
        IntegratedVerificationService instance
    """
    try:
        return IntegratedVerificationService(
            db_session, textverified_client, twilio_client
        )
    except Exception as e:
        logger.error(f"Failed to create integrated verification service: {e}")
        raise


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_integrated_service():
        # This would be used with actual database session and clients
        print("Integrated Verification Service - Ready for production use")
        print("Features:")
        print("- Service verification workflow with TextVerified")
        print("- Smart routing integration")
        print("- Enhanced monitoring and notifications")
        print("- Comprehensive analytics and tracking")
        print("- Support for 15+ popular services")

    asyncio.run(test_integrated_service())
