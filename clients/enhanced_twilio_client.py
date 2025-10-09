#!/usr/bin/env python3
"""
Enhanced Twilio Client for namaskah Communication Platform
Provides advanced SMS, voice, and number management capabilities
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import phonenumbers
from phonenumbers import carrier, geocoder
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

logger = logging.getLogger(__name__)


class EnhancedTwilioClient:
    """
    Enhanced Twilio client with advanced SMS, voice, and number management capabilities
    """

    def __init__(self, account_sid: str, auth_token: str):
        """
        Initialize the enhanced Twilio client

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.client = Client(account_sid, auth_token)

        # Cache for frequently accessed data
        self.country_cache = {}
        self.number_cache = {}

        logger.info("Enhanced Twilio client initialized successfully")

    # SMS Methods
    async def send_sms(
        self, from_number: str, to_number: str, message: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Send SMS message with enhanced error handling and logging

        Args:
            from_number: Sender phone number
            to_number: Recipient phone number
            message: Message content
            **kwargs: Additional Twilio parameters

        Returns:
            Dictionary with message details and status
        """
        try:
            # Validate phone numbers
            self._validate_phone_number(from_number)
            self._validate_phone_number(to_number)

            # Send message
            twilio_message = self.client.messages.create(
                body=message, from_=from_number, to=to_number, **kwargs
            )

            result = {
                "sid": twilio_message.sid,
                "from_number": from_number,
                "to_number": to_number,
                "message": message,
                "status": twilio_message.status,
                "direction": "outbound",
                "date_created": (
                    twilio_message.date_created.isoformat()
                    if twilio_message.date_created
                    else None
                ),
                "price": twilio_message.price,
                "price_unit": twilio_message.price_unit,
                "error_code": twilio_message.error_code,
                "error_message": twilio_message.error_message,
            }

            logger.info(f"SMS sent successfully: {twilio_message.sid} to {to_number}")
            return result

        except TwilioRestException as e:
            logger.error(f"Twilio SMS error: {e.msg} (Code: {e.code})")
            raise Exception(f"SMS sending failed: {e.msg}")
        except Exception as e:
            logger.error(f"SMS sending error: {e}")
            raise Exception(f"SMS sending failed: {str(e)}")

    async def receive_sms_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming SMS webhook data

        Args:
            webhook_data: Webhook payload from Twilio

        Returns:
            Processed message data
        """
        try:
            processed_data = {
                "sid": webhook_data.get("MessageSid"),
                "from_number": webhook_data.get("From"),
                "to_number": webhook_data.get("To"),
                "message": webhook_data.get("Body"),
                "status": webhook_data.get("MessageStatus"),
                "direction": "inbound",
                "date_created": datetime.now().isoformat(),
                "media_count": int(webhook_data.get("NumMedia", 0)),
                "media_urls": [],
            }

            # Process media attachments if any
            media_count = int(webhook_data.get("NumMedia", 0))
            for i in range(media_count):
                media_url = webhook_data.get(f"MediaUrl{i}")
                if media_url:
                    processed_data["media_urls"].append(media_url)

            logger.info(
                f"Processed incoming SMS: {processed_data['sid']} from {processed_data['from_number']}"
            )
            return processed_data

        except Exception as e:
            logger.error(f"Error processing SMS webhook: {e}")
            raise Exception(f"Webhook processing failed: {str(e)}")

    # Voice Call Methods
    async def make_call(
        self, from_number: str, to_number: str, twiml_url: str = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Make an outbound voice call

        Args:
            from_number: Caller phone number
            to_number: Recipient phone number
            twiml_url: TwiML URL for call instructions
            **kwargs: Additional Twilio parameters

        Returns:
            Dictionary with call details
        """
        try:
            # Validate phone numbers
            self._validate_phone_number(from_number)
            self._validate_phone_number(to_number)

            # Default TwiML if none provided
            if not twiml_url:
                twiml_url = "http://demo.twilio.com/docs/voice.xml"

            # Make call
            call = self.client.calls.create(
                to=to_number, from_=from_number, url=twiml_url, **kwargs
            )

            result = {
                "sid": call.sid,
                "from_number": from_number,
                "to_number": to_number,
                "status": call.status,
                "direction": "outbound",
                "date_created": (
                    call.date_created.isoformat() if call.date_created else None
                ),
                "duration": call.duration,
                "price": call.price,
                "price_unit": call.price_unit,
            }

            logger.info(f"Call initiated: {call.sid} to {to_number}")
            return result

        except TwilioRestException as e:
            logger.error(f"Twilio call error: {e.msg} (Code: {e.code})")
            raise Exception(f"Call failed: {e.msg}")
        except Exception as e:
            logger.error(f"Call error: {e}")
            raise Exception(f"Call failed: {str(e)}")

    async def receive_call_webhook(
        self, webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process incoming call webhook data

        Args:
            webhook_data: Webhook payload from Twilio

        Returns:
            Processed call data
        """
        try:
            processed_data = {
                "sid": webhook_data.get("CallSid"),
                "from_number": webhook_data.get("From"),
                "to_number": webhook_data.get("To"),
                "status": webhook_data.get("CallStatus"),
                "direction": webhook_data.get("Direction", "inbound"),
                "date_created": datetime.now().isoformat(),
                "caller_name": webhook_data.get("CallerName"),
                "caller_city": webhook_data.get("CallerCity"),
                "caller_state": webhook_data.get("CallerState"),
                "caller_country": webhook_data.get("CallerCountry"),
            }

            logger.info(
                f"Processed incoming call: {processed_data['sid']} from {processed_data['from_number']}"
            )
            return processed_data

        except Exception as e:
            logger.error(f"Error processing call webhook: {e}")
            raise Exception(f"Call webhook processing failed: {str(e)}")

    async def record_call(self, call_sid: str, **kwargs) -> Dict[str, Any]:
        """
        Start recording a call

        Args:
            call_sid: Call SID to record
            **kwargs: Additional recording parameters

        Returns:
            Recording details
        """
        try:
            recording = self.client.calls(call_sid).recordings.create(**kwargs)

            result = {
                "recording_sid": recording.sid,
                "call_sid": call_sid,
                "status": recording.status,
                "date_created": (
                    recording.date_created.isoformat()
                    if recording.date_created
                    else None
                ),
                "duration": recording.duration,
                "uri": recording.uri,
            }

            logger.info(f"Call recording started: {recording.sid} for call {call_sid}")
            return result

        except TwilioRestException as e:
            logger.error(f"Call recording error: {e.msg} (Code: {e.code})")
            raise Exception(f"Call recording failed: {e.msg}")

    async def forward_call(
        self, call_sid: str, forward_to: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Forward a call to another number

        Args:
            call_sid: Call SID to forward
            forward_to: Number to forward to
            **kwargs: Additional parameters

        Returns:
            Forward operation result
        """
        try:
            # Update call to redirect to new number
            call = self.client.calls(call_sid).update(
                url=f"http://twimlets.com/forward?PhoneNumber={forward_to}", **kwargs
            )

            result = {
                "call_sid": call_sid,
                "forwarded_to": forward_to,
                "status": call.status,
                "date_updated": datetime.now().isoformat(),
            }

            logger.info(f"Call forwarded: {call_sid} to {forward_to}")
            return result

        except TwilioRestException as e:
            logger.error(f"Call forwarding error: {e.msg} (Code: {e.code})")
            raise Exception(f"Call forwarding failed: {e.msg}")

    async def create_conference(self, conference_name: str, **kwargs) -> Dict[str, Any]:
        """
        Create a conference call

        Args:
            conference_name: Name of the conference
            **kwargs: Additional conference parameters

        Returns:
            Conference details
        """
        try:
            # Create conference room
            conference = self.client.conferences.create(
                friendly_name=conference_name, **kwargs
            )

            result = {
                "conference_sid": conference.sid,
                "friendly_name": conference.friendly_name,
                "status": conference.status,
                "date_created": (
                    conference.date_created.isoformat()
                    if conference.date_created
                    else None
                ),
                "participant_count": 0,
            }

            logger.info(f"Conference created: {conference.sid} ({conference_name})")
            return result

        except TwilioRestException as e:
            logger.error(f"Conference creation error: {e.msg} (Code: {e.code})")
            raise Exception(f"Conference creation failed: {e.msg}")

    # Phone Number Management Methods
    async def search_available_numbers(
        self, country_code: str, area_code: str = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for available phone numbers

        Args:
            country_code: ISO country code (e.g., 'US', 'GB')
            area_code: Area code for local numbers
            **kwargs: Additional search parameters

        Returns:
            List of available numbers
        """
        try:
            search_params = {
                "limit": kwargs.get("limit", 20),
                "sms_enabled": kwargs.get("sms_enabled", True),
                "voice_enabled": kwargs.get("voice_enabled", True),
            }

            if area_code:
                search_params["area_code"] = area_code

            # Search for numbers
            available_numbers = self.client.available_phone_numbers(
                country_code
            ).local.list(**search_params)

            results = []
            for number in available_numbers:
                number_info = {
                    "phone_number": number.phone_number,
                    "friendly_name": number.friendly_name,
                    "country_code": country_code,
                    "locality": number.locality,
                    "region": number.region,
                    "postal_code": number.postal_code,
                    "iso_country": number.iso_country,
                    "capabilities": {
                        "voice": number.capabilities.get("voice", False),
                        "sms": number.capabilities.get("SMS", False),
                        "mms": number.capabilities.get("MMS", False),
                    },
                    "beta": number.beta,
                    "lata": number.lata,
                    "rate_center": number.rate_center,
                }
                results.append(number_info)

            logger.info(f"Found {len(results)} available numbers in {country_code}")
            return results

        except TwilioRestException as e:
            logger.error(f"Number search error: {e.msg} (Code: {e.code})")
            raise Exception(f"Number search failed: {e.msg}")

    async def purchase_number(self, phone_number: str, **kwargs) -> Dict[str, Any]:
        """
        Purchase a phone number

        Args:
            phone_number: Phone number to purchase
            **kwargs: Additional purchase parameters

        Returns:
            Purchase result with number details
        """
        try:
            # Purchase the number
            incoming_phone_number = self.client.incoming_phone_numbers.create(
                phone_number=phone_number, **kwargs
            )

            result = {
                "sid": incoming_phone_number.sid,
                "phone_number": incoming_phone_number.phone_number,
                "friendly_name": incoming_phone_number.friendly_name,
                "country_code": incoming_phone_number.iso_country,
                "status": "purchased",
                "date_created": (
                    incoming_phone_number.date_created.isoformat()
                    if incoming_phone_number.date_created
                    else None
                ),
                "capabilities": {
                    "voice": incoming_phone_number.capabilities.get("voice", False),
                    "sms": incoming_phone_number.capabilities.get("sms", False),
                    "mms": incoming_phone_number.capabilities.get("mms", False),
                },
                "voice_url": incoming_phone_number.voice_url,
                "sms_url": incoming_phone_number.sms_url,
            }

            logger.info(
                f"Number purchased successfully: {phone_number} (SID: {incoming_phone_number.sid})"
            )
            return result

        except TwilioRestException as e:
            logger.error(f"Number purchase error: {e.msg} (Code: {e.code})")
            raise Exception(f"Number purchase failed: {e.msg}")

    async def release_number(self, phone_number_sid: str) -> bool:
        """
        Release (delete) a purchased phone number

        Args:
            phone_number_sid: SID of the phone number to release

        Returns:
            True if successful
        """
        try:
            self.client.incoming_phone_numbers(phone_number_sid).delete()
            logger.info(f"Number released successfully: {phone_number_sid}")
            return True

        except TwilioRestException as e:
            logger.error(f"Number release error: {e.msg} (Code: {e.code})")
            raise Exception(f"Number release failed: {e.msg}")

    async def list_owned_numbers(self) -> List[Dict[str, Any]]:
        """
        List all owned phone numbers

        Returns:
            List of owned numbers with details
        """
        try:
            owned_numbers = self.client.incoming_phone_numbers.list()

            results = []
            for number in owned_numbers:
                number_info = {
                    "sid": number.sid,
                    "phone_number": number.phone_number,
                    "friendly_name": number.friendly_name,
                    "country_code": number.iso_country,
                    "date_created": (
                        number.date_created.isoformat() if number.date_created else None
                    ),
                    "capabilities": {
                        "voice": number.capabilities.get("voice", False),
                        "sms": number.capabilities.get("sms", False),
                        "mms": number.capabilities.get("mms", False),
                    },
                    "voice_url": number.voice_url,
                    "sms_url": number.sms_url,
                    "status_callback": number.status_callback,
                }
                results.append(number_info)

            logger.info(f"Retrieved {len(results)} owned numbers")
            return results

        except TwilioRestException as e:
            logger.error(f"Error listing owned numbers: {e.msg} (Code: {e.code})")
            raise Exception(f"Failed to list owned numbers: {e.msg}")

    # Utility Methods
    def _validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format

        Args:
            phone_number: Phone number to validate

        Returns:
            True if valid

        Raises:
            Exception if invalid
        """
        try:
            parsed_number = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise Exception(f"Invalid phone number format: {phone_number}")
            return True
        except phonenumbers.NumberParseException as e:
            raise Exception(f"Phone number parsing error: {e}")

    def get_number_info(self, phone_number: str) -> Dict[str, Any]:
        """
        Get detailed information about a phone number

        Args:
            phone_number: Phone number to analyze

        Returns:
            Number information including country, carrier, etc.
        """
        try:
            parsed_number = phonenumbers.parse(phone_number, None)

            info = {
                "phone_number": phone_number,
                "country_code": parsed_number.country_code,
                "national_number": parsed_number.national_number,
                "country_name": geocoder.description_for_number(parsed_number, "en"),
                "carrier": carrier.name_for_number(parsed_number, "en"),
                "number_type": phonenumbers.number_type(parsed_number),
                "is_valid": phonenumbers.is_valid_number(parsed_number),
                "is_possible": phonenumbers.is_possible_number(parsed_number),
            }

            return info

        except phonenumbers.NumberParseException as e:
            logger.error(f"Error parsing phone number {phone_number}: {e}")
            return {"error": str(e)}

    async def get_account_balance(self) -> Dict[str, Any]:
        """
        Get Twilio account balance and usage

        Returns:
            Account balance and usage information
        """
        try:
            account = self.client.api.accounts(self.account_sid).fetch()

            balance_info = {
                "account_sid": account.sid,
                "friendly_name": account.friendly_name,
                "status": account.status,
                "type": account.type,
                "date_created": (
                    account.date_created.isoformat() if account.date_created else None
                ),
                "date_updated": (
                    account.date_updated.isoformat() if account.date_updated else None
                ),
            }

            logger.info("Retrieved account balance information")
            return balance_info

        except TwilioRestException as e:
            logger.error(f"Error getting account balance: {e.msg} (Code: {e.code})")
            raise Exception(f"Failed to get account balance: {e.msg}")


# Factory function for creating enhanced client
def create_enhanced_twilio_client(
    account_sid: str = None, auth_token: str = None
) -> Union[EnhancedTwilioClient, None]:
    """
    Factory function to create enhanced Twilio client

    Args:
        account_sid: Twilio Account SID
        auth_token: Twilio Auth Token

    Returns:
        EnhancedTwilioClient instance or None if credentials missing
    """
    if not account_sid or not auth_token:
        logger.warning("Twilio credentials not provided, enhanced client not available")
        return None

    try:
        return EnhancedTwilioClient(account_sid, auth_token)
    except Exception as e:
        logger.error(f"Failed to create enhanced Twilio client: {e}")
        return None


# Example usage
if __name__ == "__main__":
    import asyncio

    # Load from environment
    ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

    async def test_enhanced_client():
        if not ACCOUNT_SID or not AUTH_TOKEN:
            print("Twilio credentials not found in environment")
            return

        client = EnhancedTwilioClient(ACCOUNT_SID, AUTH_TOKEN)

        try:
            # Test account balance
            balance = await client.get_account_balance()
            print(f"Account: {balance}")

            # Test number search
            numbers = await client.search_available_numbers("US", limit=5)
            print(f"Available numbers: {len(numbers)}")

            # Test owned numbers
            owned = await client.list_owned_numbers()
            print(f"Owned numbers: {len(owned)}")

        except Exception as e:
            print(f"Error: {e}")

    # Run test
    asyncio.run(test_enhanced_client())
