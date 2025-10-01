#!/usr/bin/env python3
"""
TextVerified API Client
Requirements: requests
"""
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class TextVerifiedClient:
    """Client for TextVerified API v2"""

    def __init__(self, api_key: str, email: str, webhook_url: str = None):
        self.base_url = "https://www.textverified.com"
        self.api_key = api_key
        self.email = email
        self.webhook_url = webhook_url
        self.cache = {}  # Token cache

    def _is_bearer_token_expired(self) -> bool:
        """Check if the cached bearer token is expired"""
        token_cache = self.cache.get("token")
        if not token_cache:
            return True

        expiration_str = token_cache.get("expiresAt")
        if expiration_str:
            try:
                expiration = datetime.fromisoformat(
                    expiration_str.replace("Z", "+00:00")
                )
                return datetime.now(timezone.utc) >= expiration
            except ValueError:
                logger.warning(f"Invalid expiration format: {expiration_str}")
                return True
        return True

    def _get_token_from_cache(self) -> Optional[str]:
        """Get token from cache if available"""
        token_cache = self.cache.get("token")
        return token_cache.get("token") if token_cache else None

    async def generate_bearer_token(self) -> str:
        """
        Generate bearer token for authentication.
        Checks cache before making a request.
        """
        # Check if we have a valid cached token
        if not self._is_bearer_token_expired():
            cached_token = self._get_token_from_cache()
            if cached_token:
                return cached_token

        # Generate new token
        headers = {"X-API-KEY": self.api_key, "X-API-USERNAME": self.email}

        try:
            response = requests.post(
                f"{self.base_url}/api/pub/v2/auth", headers=headers
            )
            response.raise_for_status()

            data = response.json()
            self.cache["token"] = data  # Cache the token data
            token = data.get("token")

            logger.info("Successfully generated new bearer token")
            return token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate bearer token: {e}")
            raise Exception(f"Authentication failed: {e}")

    async def check_balance(self) -> float:
        """
        Get current account balance
        Returns: Current balance as float
        """
        bearer_token = await self.generate_bearer_token()
        headers = {"Authorization": f"Bearer {bearer_token}"}

        try:
            response = requests.get(
                f"{self.base_url}/api/pub/v2/account/me", headers=headers
            )
            response.raise_for_status()

            data = response.json()
            balance = data.get("currentBalance", 0.0)
            logger.info(f"Current balance: {balance}")
            return float(balance)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check balance: {e}")
            raise Exception(f"Balance check failed: {e}")

    async def get_service_list(
        self, number_type: str = "mobile", reservation_type: str = "verification"
    ) -> List[Dict[str, Any]]:
        """
        Get list of available services
        Args:
            number_type: mobile, voip, landline
            reservation_type: renewable, nonrenewable, verification
        Returns: List of available services
        """
        bearer_token = await self.generate_bearer_token()
        headers = {"Authorization": f"Bearer {bearer_token}"}

        params = {"numberType": number_type, "reservationType": reservation_type}

        try:
            response = requests.get(
                f"{self.base_url}/api/pub/v2/services", headers=headers, params=params
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Retrieved {len(data)} services")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get service list: {e}")
            raise Exception(f"Service list retrieval failed: {e}")

    async def create_verification(
        self, service_name: str, capability: str = "sms"
    ) -> str:
        """
        Create a verification for a specific service
        Args:
            service_name: Name of the service (e.g., 'whatsapp', 'googlemessenger')
            capability: sms, voice, smsAndVoiceCombo
        Returns: Verification ID
        """
        bearer_token = await self.generate_bearer_token()
        headers = {"Authorization": f"Bearer {bearer_token}"}

        json_data = {
            "serviceName": service_name,
            "capability": capability,
        }
        
        # Add webhook URL if configured
        if self.webhook_url:
            json_data["webhookUrl"] = self.webhook_url

        try:
            response = requests.post(
                f"{self.base_url}/api/pub/v2/verifications",
                headers=headers,
                json=json_data,
            )
            response.raise_for_status()

            # Extract verification ID from location header
            location = response.headers.get("Location")
            if location:
                verification_id = location.split("/")[-1]
                logger.info(
                    f"Created verification {verification_id} for service {service_name}"
                )
                return verification_id
            else:
                # Fallback to response data
                data = response.json()
                href = data.get("href", "")
                verification_id = href.split("/")[-1] if href else ""
                if verification_id:
                    logger.info(
                        f"Created verification {verification_id} for service {service_name}"
                    )
                    return verification_id
                else:
                    raise Exception("No verification ID returned")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create verification for {service_name}: {e}")
            raise Exception(f"Verification creation failed: {e}")

    async def get_verification_details(self, verification_id: str) -> Dict[str, Any]:
        """
        Get verification details including phone number and status
        Args:
            verification_id: The verification ID
        Returns: Verification details dictionary
        """
        bearer_token = await self.generate_bearer_token()
        headers = {"Authorization": f"Bearer {bearer_token}"}

        try:
            response = requests.get(
                f"{self.base_url}/api/pub/v2/verifications/{verification_id}",
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Retrieved verification details for {verification_id}")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to get verification details for {verification_id}: {e}"
            )
            raise Exception(f"Verification details retrieval failed: {e}")

    async def get_verification_number(self, verification_id: str) -> str:
        """
        Get the phone number for a verification
        Args:
            verification_id: The verification ID
        Returns: Phone number string
        """
        details = await self.get_verification_details(verification_id)
        number = details.get("number", "")
        if not number:
            raise Exception(f"No phone number found for verification {verification_id}")
        return number

    async def get_sms_messages(self, verification_id: str) -> List[str]:
        """
        Get SMS messages for a verification
        Args:
            verification_id: The verification ID
        Returns: List of SMS message contents
        """
        bearer_token = await self.generate_bearer_token()
        headers = {"Authorization": f"Bearer {bearer_token}"}

        try:
            response = requests.get(
                f"{self.base_url}/api/pub/v2/sms?reservationId={verification_id}",
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            messages = []

            sms_data = data.get("data", [])
            for sms in sms_data:
                content = sms.get("smsContent", "")
                if content:
                    messages.append(content)

            logger.info(
                f"Retrieved {len(messages)} SMS messages for verification {verification_id}"
            )
            return messages

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get SMS messages for {verification_id}: {e}")
            raise Exception(f"SMS retrieval failed: {e}")

    async def cancel_verification(self, verification_id: str) -> bool:
        """
        Cancel a verification
        Args:
            verification_id: The verification ID to cancel
        Returns: True if successful
        """
        bearer_token = await self.generate_bearer_token()
        headers = {"Authorization": f"Bearer {bearer_token}"}

        try:
            response = requests.post(
                f"{self.base_url}/api/pub/v2/verifications/{verification_id}/cancel",
                headers=headers,
            )
            response.raise_for_status()

            logger.info(f"Successfully cancelled verification {verification_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to cancel verification {verification_id}: {e}")
            raise Exception(f"Verification cancellation failed: {e}")

    async def report_verification(self, verification_id: str) -> bool:
        """
        Report a verification (for issues)
        Args:
            verification_id: The verification ID to report
        Returns: True if successful
        """
        bearer_token = await self.generate_bearer_token()
        headers = {"Authorization": f"Bearer {bearer_token}"}

        try:
            response = requests.post(
                f"{self.base_url}/api/pub/v2/verifications/{verification_id}/report",
                headers=headers,
            )
            response.raise_for_status()

            logger.info(f"Successfully reported verification {verification_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report verification {verification_id}: {e}")
            raise Exception(f"Verification reporting failed: {e}")

    def check_verification_completed(self, verification_data: Dict[str, Any]) -> bool:
        """
        Check if verification is completed based on verification data
        Args:
            verification_data: Data from get_verification_details
        Returns: True if verification is completed
        """
        verification_state = verification_data.get("state", "")

        if verification_state == "verificationPending":
            logger.info("Verification is pending")
            return False
        elif verification_state == "verificationCompleted":
            logger.info("Verification is completed")
            return True
        else:
            logger.warning(f"Unknown verification state: {verification_state}")
            return False

    async def poll_for_verification(
        self, verification_id: str, timeout: int = 300, interval: int = 10
    ) -> bool:
        """
        Poll for verification completion
        Args:
            verification_id: The verification ID to poll
            timeout: Maximum time to wait in seconds
            interval: Polling interval in seconds
        Returns: True if verification completed within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                details = await self.get_verification_details(verification_id)
                if self.check_verification_completed(details):
                    return True

                logger.info(
                    f"Verification {verification_id} still pending, waiting {interval} seconds..."
                )
                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error during polling: {e}")
                time.sleep(interval)

        logger.warning(
            f"Verification {verification_id} timed out after {timeout} seconds"
        )
        return False


# Example usage and testing
if __name__ == "__main__":
    import asyncio

    # Load from environment variables
    API_KEY = os.getenv(
        "TEXTVERIFIED_API_KEY",
        "MSZ9Lr6XnKPTBNjnrHjD6mXi0ESmYUX7pdDEve9TbK8msE3hag6N1OQcPYREg",
    )
    EMAIL = os.getenv("TEXTVERIFIED_EMAIL", "huff_06psalm@icloud.com")

    async def test_client():
        client = TextVerifiedClient(API_KEY, EMAIL)

        try:
            # Check balance
            balance = await client.check_balance()
            print(f"Account balance: ${balance}")

            # Get available services
            services = await client.get_service_list()
            print(f"Available services: {len(services)}")

            # Example verification flow (commented out to avoid charges)
            # verification_id = await client.create_verification("googlemessenger")
            # number = await client.get_verification_number(verification_id)
            # print(f"Use this number: {number}")
            #
            # # Poll for messages
            # completed = await client.poll_for_verification(verification_id, timeout=60)
            # if completed:
            #     messages = await client.get_sms_messages(verification_id)
            #     print(f"Received messages: {messages}")

        except Exception as e:
            print(f"Error: {e}")

    # Run the test
    asyncio.run(test_client())
