"""
Unified Client Interface for CumApp
Provides a single interface for all external services with automatic fallback to mocks
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

from .textverified_client import TextVerifiedClient
from .groq_client import GroqAIClient
from .mock_twilio_client import MockTwilioClient, create_twilio_client
from .enhanced_twilio_client import EnhancedTwilioClient, create_enhanced_twilio_client

logger = logging.getLogger(__name__)


class UnifiedServiceClient:
    """
    Unified client that manages all external service integrations
    Automatically falls back to mock services when real credentials are not available
    """

    def __init__(self):
        """Initialize all service clients with automatic fallback"""
        self.textverified_client = self._init_textverified()
        self.twilio_client = self._init_twilio()
        self.groq_client = self._init_groq()
        
        # Service availability flags
        self.services_available = {
            'textverified': self.textverified_client is not None,
            'twilio': isinstance(self.twilio_client, EnhancedTwilioClient),
            'groq': self.groq_client is not None
        }
        
        logger.info(f"Unified client initialized. Available services: {self.services_available}")

    def _init_textverified(self) -> Optional[TextVerifiedClient]:
        """Initialize TextVerified client"""
        api_key = os.getenv('TEXTVERIFIED_API_KEY')
        email = os.getenv('TEXTVERIFIED_EMAIL')
        webhook_url = os.getenv('TEXTVERIFIED_WEBHOOK_URL')
        
        if api_key and email:
            try:
                client = TextVerifiedClient(api_key, email, webhook_url)
                logger.info("TextVerified client initialized successfully")
                return client
            except Exception as e:
                logger.warning(f"Failed to initialize TextVerified client: {e}")
        else:
            logger.info("TextVerified credentials not found, using mock mode")
        
        return None

    def _init_twilio(self) -> Union[EnhancedTwilioClient, MockTwilioClient]:
        """Initialize Twilio client with fallback to mock"""
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        use_mock = os.getenv('USE_MOCK_TWILIO', 'true').lower() == 'true'
        
        if not use_mock and account_sid and auth_token:
            try:
                client = EnhancedTwilioClient(account_sid, auth_token)
                logger.info("Enhanced Twilio client initialized successfully")
                return client
            except Exception as e:
                logger.warning(f"Failed to initialize Twilio client, falling back to mock: {e}")
        
        # Fallback to mock client
        mock_client = MockTwilioClient(account_sid, auth_token)
        logger.info("Mock Twilio client initialized")
        return mock_client

    def _init_groq(self) -> Optional[GroqAIClient]:
        """Initialize Groq AI client"""
        api_key = os.getenv('GROQ_API_KEY')
        model = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
        
        if api_key:
            try:
                client = GroqAIClient(api_key, model)
                logger.info("Groq AI client initialized successfully")
                return client
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")
        else:
            logger.info("Groq API key not found, AI features disabled")
        
        return None

    # SMS Methods
    async def send_sms(self, from_number: str, to_number: str, message: str) -> Dict[str, Any]:
        """Send SMS using available Twilio client"""
        try:
            if isinstance(self.twilio_client, EnhancedTwilioClient):
                return await self.twilio_client.send_sms(from_number, to_number, message)
            else:
                # Mock client
                mock_message = self.twilio_client.messages.create(
                    body=message, from_=from_number, to=to_number
                )
                return {
                    'sid': mock_message.sid,
                    'from_number': from_number,
                    'to_number': to_number,
                    'message': message,
                    'status': 'sent',
                    'mock': True
                }
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            raise

    async def receive_sms_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming SMS webhook"""
        try:
            if isinstance(self.twilio_client, EnhancedTwilioClient):
                return await self.twilio_client.receive_sms_webhook(webhook_data)
            else:
                # Mock processing
                return {
                    'sid': webhook_data.get('MessageSid', 'mock_sid'),
                    'from_number': webhook_data.get('From'),
                    'to_number': webhook_data.get('To'),
                    'message': webhook_data.get('Body'),
                    'status': 'received',
                    'mock': True
                }
        except Exception as e:
            logger.error(f"SMS webhook processing failed: {e}")
            raise

    # Verification Methods
    async def create_verification(self, service_name: str) -> str:
        """Create verification using TextVerified or mock"""
        try:
            if self.textverified_client:
                return await self.textverified_client.create_verification(service_name)
            else:
                # Mock verification
                import uuid
                mock_id = f"mock_verification_{uuid.uuid4().hex[:8]}"
                logger.info(f"Created mock verification: {mock_id} for {service_name}")
                return mock_id
        except Exception as e:
            logger.error(f"Verification creation failed: {e}")
            raise

    async def get_verification_number(self, verification_id: str) -> str:
        """Get verification phone number"""
        try:
            if self.textverified_client:
                return await self.textverified_client.get_verification_number(verification_id)
            else:
                # Mock number
                mock_number = "+1555000001"
                logger.info(f"Mock verification number: {mock_number}")
                return mock_number
        except Exception as e:
            logger.error(f"Failed to get verification number: {e}")
            raise

    async def get_verification_messages(self, verification_id: str) -> List[str]:
        """Get SMS messages for verification"""
        try:
            if self.textverified_client:
                return await self.textverified_client.get_sms_messages(verification_id)
            else:
                # Mock messages
                mock_messages = [
                    f"Your verification code is: 123456",
                    f"Code expires in 10 minutes"
                ]
                logger.info(f"Mock verification messages: {len(mock_messages)} messages")
                return mock_messages
        except Exception as e:
            logger.error(f"Failed to get verification messages: {e}")
            raise

    async def get_available_services(self) -> List[Dict[str, Any]]:
        """Get list of available verification services"""
        try:
            if self.textverified_client:
                return await self.textverified_client.get_service_list()
            else:
                # Mock services
                mock_services = [
                    {'name': 'whatsapp', 'displayName': 'WhatsApp', 'cost': 0.10},
                    {'name': 'googlemessenger', 'displayName': 'Google', 'cost': 0.08},
                    {'name': 'telegram', 'displayName': 'Telegram', 'cost': 0.12},
                    {'name': 'discord', 'displayName': 'Discord', 'cost': 0.09},
                    {'name': 'instagram', 'displayName': 'Instagram', 'cost': 0.11}
                ]
                logger.info(f"Mock services: {len(mock_services)} available")
                return mock_services
        except Exception as e:
            logger.error(f"Failed to get available services: {e}")
            raise

    # AI Methods
    async def suggest_response(self, conversation_history: List[Dict[str, str]]) -> str:
        """Get AI-powered response suggestion"""
        try:
            if self.groq_client:
                return await self.groq_client.suggest_sms_response(conversation_history)
            else:
                # Fallback response
                return "Thank you for your message. How can I help you today?"
        except Exception as e:
            logger.error(f"AI response suggestion failed: {e}")
            return "I'd be happy to help with that."

    async def analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze message intent and sentiment"""
        try:
            if self.groq_client:
                return await self.groq_client.analyze_message_intent(message)
            else:
                # Mock analysis
                return {
                    'intent': 'general',
                    'sentiment': 'neutral',
                    'urgency': 'medium',
                    'suggested_tone': 'casual',
                    'confidence': 0.5,
                    'mock': True
                }
        except Exception as e:
            logger.error(f"Message analysis failed: {e}")
            return {
                'intent': 'unknown',
                'sentiment': 'neutral',
                'urgency': 'medium',
                'suggested_tone': 'casual',
                'confidence': 0.0
            }

    async def generate_verification_message(self, service_name: str, code: str) -> str:
        """Generate user-friendly verification message"""
        try:
            if self.groq_client:
                return await self.groq_client.generate_verification_message(service_name, code)
            else:
                # Simple template
                return f"✅ Your {service_name} verification code is: {code}"
        except Exception as e:
            logger.error(f"Verification message generation failed: {e}")
            return f"Your {service_name} verification code: {code}"

    # Phone Number Management
    async def search_phone_numbers(self, country_code: str = 'US') -> List[Dict[str, Any]]:
        """Search for available phone numbers"""
        try:
            if isinstance(self.twilio_client, EnhancedTwilioClient):
                return await self.twilio_client.search_available_numbers(country_code)
            else:
                # Mock numbers
                return self.twilio_client.get_available_phone_numbers(country_code)
        except Exception as e:
            logger.error(f"Phone number search failed: {e}")
            raise

    async def purchase_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """Purchase a phone number"""
        try:
            if isinstance(self.twilio_client, EnhancedTwilioClient):
                return await self.twilio_client.purchase_number(phone_number)
            else:
                # Mock purchase
                return self.twilio_client.purchase_phone_number(phone_number)
        except Exception as e:
            logger.error(f"Phone number purchase failed: {e}")
            raise

    async def list_owned_numbers(self) -> List[Dict[str, Any]]:
        """List owned phone numbers"""
        try:
            if isinstance(self.twilio_client, EnhancedTwilioClient):
                return await self.twilio_client.list_owned_numbers()
            else:
                # Mock owned numbers
                return [
                    {
                        'phone_number': '+1555000001',
                        'friendly_name': 'Mock Number 1',
                        'country_code': 'US',
                        'status': 'active',
                        'mock': True
                    }
                ]
        except Exception as e:
            logger.error(f"Failed to list owned numbers: {e}")
            raise

    # Utility Methods
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            'textverified': {
                'available': self.services_available['textverified'],
                'type': 'real' if self.services_available['textverified'] else 'mock'
            },
            'twilio': {
                'available': True,  # Always available (mock or real)
                'type': 'real' if self.services_available['twilio'] else 'mock'
            },
            'groq': {
                'available': self.services_available['groq'],
                'type': 'real' if self.services_available['groq'] else 'disabled'
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        health_status = {}
        
        # Check TextVerified
        try:
            if self.textverified_client:
                balance = await self.textverified_client.check_balance()
                health_status['textverified'] = {'status': 'healthy', 'balance': balance}
            else:
                health_status['textverified'] = {'status': 'mock', 'balance': 100.0}
        except Exception as e:
            health_status['textverified'] = {'status': 'error', 'error': str(e)}

        # Check Twilio
        try:
            if isinstance(self.twilio_client, EnhancedTwilioClient):
                account = await self.twilio_client.get_account_balance()
                health_status['twilio'] = {'status': 'healthy', 'account': account}
            else:
                stats = self.twilio_client.get_usage_statistics()
                health_status['twilio'] = {'status': 'mock', 'stats': stats}
        except Exception as e:
            health_status['twilio'] = {'status': 'error', 'error': str(e)}

        # Check Groq
        if self.groq_client:
            try:
                # Simple test call
                test_response = await self.groq_client.suggest_sms_response([
                    {'role': 'user', 'content': 'Hello'}
                ])
                health_status['groq'] = {'status': 'healthy', 'test_response': len(test_response)}
            except Exception as e:
                health_status['groq'] = {'status': 'error', 'error': str(e)}
        else:
            health_status['groq'] = {'status': 'disabled'}

        return health_status


# Global instance
_unified_client = None

def get_unified_client() -> UnifiedServiceClient:
    """Get singleton instance of unified client"""
    global _unified_client
    if _unified_client is None:
        _unified_client = UnifiedServiceClient()
    return _unified_client


# Convenience functions
async def send_sms(from_number: str, to_number: str, message: str) -> Dict[str, Any]:
    """Convenience function to send SMS"""
    client = get_unified_client()
    return await client.send_sms(from_number, to_number, message)

async def create_verification(service_name: str) -> str:
    """Convenience function to create verification"""
    client = get_unified_client()
    return await client.create_verification(service_name)

async def get_ai_suggestion(conversation_history: List[Dict[str, str]]) -> str:
    """Convenience function to get AI suggestion"""
    client = get_unified_client()
    return await client.suggest_response(conversation_history)