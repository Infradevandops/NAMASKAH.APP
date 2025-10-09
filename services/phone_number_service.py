#!/usr/bin/env python3
"""
Phone Number Service for namaskah Platform
Handles phone number marketplace, purchasing, and management
"""
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from clients.enhanced_twilio_client import EnhancedTwilioClient
from models.phone_number_models import PhoneNumber
from models.user_models import User

logger = logging.getLogger(__name__)


class PhoneNumberService:
    """Service for managing phone number marketplace and subscriptions"""

    def __init__(
        self,
        db: Session,
        twilio_client: Optional[EnhancedTwilioClient] = None,
        textverified_client=None,
    ):
        self.db = db
        self.textverified_client = textverified_client
        self.twilio_client = twilio_client

    async def search_available_numbers(
        self,
        country_code: str,
        area_code: Optional[str] = None,
        capabilities: List[str] = None,
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search for available phone numbers by country and area code
        """
        try:
            if self.twilio_client:
                # Use real Twilio client
                available_numbers = await self.twilio_client.search_available_numbers(
                    country_code=country_code,
                    area_code=area_code,
                    limit=limit,
                    sms_enabled="sms" in capabilities,
                    voice_enabled="voice" in capabilities,
                    mms_enabled="mms" in capabilities,
                )
                return available_numbers, len(available_numbers)
            else:
                # Fallback to mock data if no client
                logger.warning(
                    "Twilio client not available, using mock data for number search."
                )
                mock_numbers = self._generate_mock_numbers(
                    country_code, area_code, limit
                )
                return mock_numbers, len(mock_numbers)
        except Exception as e:
            logger.error(f"Error searching available numbers: {e}")
            raise

    async def purchase_phone_number(
        self, user_id: str, phone_number: str, auto_renew: bool = True
    ) -> Dict[str, Any]:
        """
        Purchase a phone number for a user
        """
        try:
            # Check if user exists and has sufficient permissions
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            # Check if number is already owned
            existing = (
                self.db.query(PhoneNumber)
                .filter(PhoneNumber.phone_number == phone_number)
                .first()
            )

            if existing and existing.status == "active":
                raise ValueError("Phone number is already owned")

            # Check user's subscription limits
            owned_count = (
                self.db.query(PhoneNumber)
                .filter(
                    and_(
                        PhoneNumber.owner_id == user_id, PhoneNumber.status == "active"
                    )
                )
                .count()
            )

            max_numbers = self._get_max_numbers_for_plan(user.subscription_plan)
            if owned_count >= max_numbers:
                raise ValueError(f"Maximum number limit reached ({max_numbers})")

            # Provision number with Twilio if client is available
            if self.twilio_client:
                provisioned_number = await self.twilio_client.purchase_number(
                    phone_number
                )
                number_details = await self._get_number_details(
                    phone_number, provider_id=provisioned_number.get("sid")
                )
            else:
                logger.warning(
                    "Twilio client not available, using mock data for number purchase."
                )
                number_details = await self._get_number_details(phone_number)

            # Create or update phone number record
            if existing:
                phone_number_record = existing
                phone_number_record.owner_id = user_id
                phone_number_record.status = "active"
                phone_number_record.purchased_at = datetime.utcnow()
            else:
                phone_number_record = PhoneNumber(
                    phone_number=phone_number,
                    country_code=number_details["country_code"],
                    area_code=number_details["area_code"],
                    region=number_details["region"],
                    provider=number_details["provider"],
                    provider_id=number_details.get(
                        "provider_id", f"mock_{phone_number}"
                    ),
                    owner_id=user_id,
                    monthly_cost=number_details["monthly_cost"],
                    sms_cost_per_message=number_details["sms_cost_per_message"],
                    voice_cost_per_minute=number_details["voice_cost_per_minute"],
                    setup_fee=str(number_details["setup_fee"]),
                    auto_renew=auto_renew,
                    status="active",
                    capabilities=json.dumps(number_details["capabilities"]),
                    purchased_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=30),  # 1 month
                    created_at=datetime.utcnow(),
                )
                self.db.add(phone_number_record)

            self.db.commit()

            # In production, would integrate with payment processor
            transaction_id = (
                f"txn_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"
            )

            return {
                "success": True,
                "message": "Phone number purchased successfully",
                "phone_number": phone_number_record.to_dict(),
                "transaction_id": transaction_id,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error purchasing phone number: {e}")
            raise

    async def get_owned_numbers(
        self, user_id: str, include_inactive: bool = False
    ) -> Tuple[List[PhoneNumber], int]:
        """
        Get phone numbers owned by a user
        """
        try:
            query = self.db.query(PhoneNumber).filter(PhoneNumber.owner_id == user_id)

            if not include_inactive:
                query = query.filter(PhoneNumber.status == "active")

            numbers = query.order_by(desc(PhoneNumber.purchased_at)).all()
            total_count = query.count()

            return numbers, total_count

        except Exception as e:
            logger.error(f"Error getting owned numbers: {e}")
            raise

    async def renew_phone_number(
        self, user_id: str, phone_number_id: str, renewal_months: int = 1
    ) -> Dict[str, Any]:
        """
        Renew a phone number subscription
        """
        try:
            # Get the phone number
            phone_number = (
                self.db.query(PhoneNumber)
                .filter(
                    and_(
                        PhoneNumber.id == phone_number_id,
                        PhoneNumber.owner_id == user_id,
                    )
                )
                .first()
            )

            if not phone_number:
                raise ValueError("Phone number not found or not owned by user")

            if phone_number.status not in ["active", "expired"]:
                raise ValueError("Phone number cannot be renewed")

            # Calculate new expiration date
            current_expires = phone_number.expires_at or datetime.utcnow()
            if current_expires < datetime.utcnow():
                # If expired, start from now
                new_expires = datetime.utcnow() + timedelta(days=30 * renewal_months)
            else:
                # If still active, extend from current expiration
                new_expires = current_expires + timedelta(days=30 * renewal_months)

            # Update the record
            phone_number.expires_at = new_expires
            phone_number.last_renewal_at = datetime.utcnow()
            phone_number.status = "active"
            phone_number.updated_at = datetime.utcnow()

            self.db.commit()

            # Calculate renewal cost
            monthly_cost = Decimal(phone_number.monthly_cost or "1.00")
            total_cost = monthly_cost * renewal_months

            transaction_id = (
                f"rnw_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"
            )

            return {
                "success": True,
                "message": f"Phone number renewed for {renewal_months} month(s)",
                "phone_number": phone_number,
                "transaction_id": transaction_id,
                "total_cost": total_cost,
                "new_expires_at": new_expires,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error renewing phone number: {e}")
            raise

    async def cancel_phone_number(
        self, user_id: str, phone_number_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a phone number subscription
        """
        try:
            # Get the phone number
            phone_number = (
                self.db.query(PhoneNumber)
                .filter(
                    and_(
                        PhoneNumber.id == phone_number_id,
                        PhoneNumber.owner_id == user_id,
                    )
                )
                .first()
            )

            if not phone_number:
                raise ValueError("Phone number not found or not owned by user")

            if phone_number.status == "cancelled":
                raise ValueError("Phone number is already cancelled")

            # Update status
            phone_number.status = "cancelled"
            phone_number.auto_renew = False
            phone_number.updated_at = datetime.utcnow()

            self.db.commit()

            return {
                "success": True,
                "message": "Phone number subscription cancelled",
                "phone_number": phone_number,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling phone number: {e}")
            raise

    async def get_usage_statistics(
        self,
        user_id: str,
        phone_number_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a phone number
        """
        try:
            # Get the phone number
            phone_number = (
                self.db.query(PhoneNumber)
                .filter(
                    and_(
                        PhoneNumber.id == phone_number_id,
                        PhoneNumber.owner_id == user_id,
                    )
                )
                .first()
            )

            if not phone_number:
                raise ValueError("Phone number not found or not owned by user")

            # Set default date range if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Calculate costs
            sms_cost_per_message = Decimal(phone_number.sms_cost_per_message or "0.01")
            voice_cost_per_minute = Decimal(
                phone_number.voice_cost_per_minute or "0.02"
            )
            monthly_cost = Decimal(phone_number.monthly_cost or "1.00")

            sms_cost = sms_cost_per_message * phone_number.monthly_sms_sent
            voice_cost = voice_cost_per_minute * phone_number.monthly_voice_minutes
            total_cost = monthly_cost + sms_cost + voice_cost

            return {
                "phone_number_id": phone_number_id,
                "phone_number": phone_number.phone_number,
                "period_start": start_date,
                "period_end": end_date,
                "usage": {
                    "sms_sent": phone_number.monthly_sms_sent,
                    "sms_received": phone_number.total_sms_received,
                    "voice_minutes": phone_number.monthly_voice_minutes,
                },
                "costs": {
                    "sms_cost": sms_cost,
                    "voice_cost": voice_cost,
                    "monthly_fee": monthly_cost,
                    "total_cost": total_cost,
                },
                "subscription": {
                    "status": phone_number.status,
                    "expires_at": phone_number.expires_at,
                    "auto_renew": phone_number.auto_renew,
                },
            }

        except Exception as e:
            logger.error(f"Error getting usage statistics: {e}")
            raise

    async def track_usage(
        self, phone_number: str, usage_type: str, amount: int = 1
    ) -> bool:
        """
        Track usage for a phone number (SMS sent/received, voice minutes)
        """
        try:
            phone_record = (
                self.db.query(PhoneNumber)
                .filter(PhoneNumber.phone_number == phone_number)
                .first()
            )

            if not phone_record:
                logger.warning(
                    f"Phone number not found for usage tracking: {phone_number}"
                )
                return False

            # Update usage counters
            if usage_type == "sms_sent":
                phone_record.total_sms_sent += amount
                phone_record.monthly_sms_sent += amount
            elif usage_type == "sms_received":
                phone_record.total_sms_received += amount
            elif usage_type == "voice_minutes":
                phone_record.total_voice_minutes += amount
                phone_record.monthly_voice_minutes += amount

            phone_record.updated_at = datetime.utcnow()
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking usage: {e}")
            return False

    # Helper methods
    def _generate_mock_numbers(
        self, country_code: str, area_code: Optional[str], limit: int
    ) -> List[Dict[str, Any]]:
        """Generate mock phone numbers for demo purposes"""
        numbers = []

        if country_code.upper() == "US":
            base_area = area_code or "555"
            for i in range(limit):
                phone_num_str = f"+1{base_area}{1000 + i:04d}"
                numbers.append(self._get_mock_number_details(phone_num_str))
        elif country_code.upper() == "GB":
            for i in range(limit):
                phone_num_str = f"+44700{100000 + i:06d}"
                numbers.append(self._get_mock_number_details(phone_num_str))
        elif country_code.upper() == "CA":
            base_area = area_code or "416"
            for i in range(limit):
                phone_num_str = f"+1{base_area}{1000 + i:04d}"
                numbers.append(self._get_mock_number_details(phone_num_str))
        else:
            # Generic international format
            for i in range(limit):
                number = f"+{country_code}555{1000 + i:04d}"
                numbers.append(number)

        return numbers

    def _extract_area_code(self, phone_number: str) -> Optional[str]:
        """Extract area code from phone number"""
        # Simple extraction for demo
        if phone_number.startswith("+1") and len(phone_number) >= 5:
            return phone_number[2:5]
        return None

    def _get_region_for_country(self, country_code: str) -> str:
        """Get region name for country code"""
        regions = {
            "US": "United States",
            "GB": "United Kingdom",
            "CA": "Canada",
            "FR": "France",
            "DE": "Germany",
            "AU": "Australia",
        }
        return regions.get(country_code.upper(), "Unknown")

    def _get_mock_number_details(
        self, phone_number: str, provider_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get mock detailed information about a phone number"""
        country_code = "US" if phone_number.startswith("+1") else "GB"

        return {
            "phone_number": phone_number,
            "friendly_name": phone_number,
            "country_code": country_code,
            "area_code": self._extract_area_code(phone_number),
            "region": self._get_region_for_country(country_code),
            "provider": "mock",
            "provider_id": provider_id or f"mock_{phone_number.replace('+', '')}",
            "monthly_cost": Decimal("1.50"),
            "sms_cost_per_message": Decimal("0.01"),
            "voice_cost_per_minute": Decimal("0.02"),
            "setup_fee": Decimal("0.00"),
            "capabilities": ["sms", "voice"],
        }

    def _get_max_numbers_for_plan(self, subscription_plan: str) -> int:
        """Get maximum number of phone numbers allowed for subscription plan"""
        limits = {"FREE": 1, "BASIC": 3, "PREMIUM": 10, "ENTERPRISE": 50}
        return limits.get(subscription_plan, 1)
