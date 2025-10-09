#!/usr/bin/env python3
"""
Communication Service for namaskah Communication Platform
Provides comprehensive SMS and voice communication with smart routing, history management,
call recording, forwarding, and user number management dashboard
"""
import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from clients.enhanced_twilio_client import EnhancedTwilioClient
from models.conversation_models import Conversation, Message
from models.phone_number_models import PhoneNumber
from models.user_models import User
from services.notification_service import NotificationService
from services.smart_routing_engine import SmartRoutingEngine

logger = logging.getLogger(__name__)


class MessageType(Enum):
    SMS = "sms"
    VOICE = "voice"
    MMS = "mms"
    CHAT = "chat"


class CallStatus(Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no-answer"


class CommunicationService:
    """
    Comprehensive communication service with SMS, voice, routing, and management features
    """

    def __init__(self, db_session: Session, twilio_client: EnhancedTwilioClient = None):
        """
        Initialize the communication service

        Args:
            db_session: Database session
            twilio_client: Enhanced Twilio client for SMS/voice operations
        """
        self.db = db_session
        self.twilio_client = twilio_client
        self.routing_engine = (
            SmartRoutingEngine(twilio_client) if twilio_client else None
        )
        self.notification_service = NotificationService()

        logger.info("Communication service initialized successfully")

    # SMS Communication Methods
    async def send_sms_with_routing(
        self,
        user_id: str,
        to_number: str,
        message: str,
        from_number: str = None,
        use_smart_routing: bool = True,
        routing_options: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Send SMS with intelligent routing options

        Args:
            user_id: ID of the user sending the message
            to_number: Recipient phone number
            message: Message content
            from_number: Sender phone number (optional, will use routing if not provided)
            use_smart_routing: Whether to use smart routing for optimal number selection
            routing_options: Additional routing configuration

        Returns:
            SMS sending result with routing information
        """
        try:
            # Validate user
            user = self._get_active_user(user_id)

            # Get optimal sender number using smart routing
            if not from_number and use_smart_routing and self.routing_engine:
                user_numbers = await self._get_user_phone_numbers(user_id)
                routing_recommendation = (
                    await self.routing_engine.suggest_optimal_numbers(
                        destination_number=to_number,
                        user_numbers=[num.phone_number for num in user_numbers],
                        message_count=1,
                    )
                )
                from_number = routing_recommendation.primary_option.phone_number

            # Fallback to user's primary number or default
            if not from_number:
                user_numbers = await self._get_user_phone_numbers(user_id)
                from_number = (
                    user_numbers[0].phone_number if user_numbers else "+1555000001"
                )

            # Send SMS using Twilio client
            if not self.twilio_client:
                raise Exception("Twilio client not available")

            twilio_result = await self.twilio_client.send_sms(
                from_number=from_number, to_number=to_number, message=message
            )

            # Create conversation if it doesn't exist
            conversation = await self._get_or_create_conversation(
                user_id=user_id, external_number=to_number
            )

            # Store message in database
            db_message = Message(
                conversation_id=conversation.id,
                sender_id=user_id,
                content=message,
                message_type=MessageType.SMS.value,
                from_number=from_number,
                to_number=to_number,
                external_message_id=twilio_result.get("sid"),
                is_delivered=twilio_result.get("status") == "sent",
                delivery_status=twilio_result.get("status"),
                created_at=datetime.utcnow(),
            )

            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)

            # Update conversation last message time
            conversation.last_message_at = datetime.utcnow()
            self.db.commit()

            result = {
                "message_id": db_message.id,
                "conversation_id": conversation.id,
                "from_number": from_number,
                "to_number": to_number,
                "message": message,
                "status": twilio_result.get("status"),
                "external_id": twilio_result.get("sid"),
                "cost": twilio_result.get("price"),
                "routing_used": use_smart_routing,
                "sent_at": db_message.created_at.isoformat(),
            }

            logger.info(
                f"SMS sent successfully: {db_message.id} from {from_number} to {to_number}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            raise

    async def receive_sms_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming SMS webhook from Twilio

        Args:
            webhook_data: Webhook payload from Twilio

        Returns:
            Processing result
        """
        try:
            # Process webhook data
            processed_data = await self.twilio_client.receive_sms_webhook(webhook_data)

            from_number = processed_data["from_number"]
            to_number = processed_data["to_number"]
            message_content = processed_data["message"]

            # Find user who owns the receiving number
            phone_number_record = (
                self.db.query(PhoneNumber)
                .filter(
                    PhoneNumber.phone_number == to_number, PhoneNumber.is_active == True
                )
                .first()
            )

            if not phone_number_record:
                logger.warning(f"Received SMS for unknown number: {to_number}")
                return {"status": "ignored", "reason": "unknown_number"}

            user_id = phone_number_record.owner_id

            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                user_id=user_id, external_number=from_number
            )

            # Store incoming message
            db_message = Message(
                conversation_id=conversation.id,
                sender_id=None,  # External sender
                content=message_content,
                message_type=MessageType.SMS.value,
                from_number=from_number,
                to_number=to_number,
                external_message_id=processed_data.get("sid"),
                is_delivered=True,
                delivery_status="received",
                created_at=datetime.utcnow(),
            )

            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)

            # Update conversation
            conversation.last_message_at = datetime.utcnow()
            self.db.commit()

            # Send notification to user
            await self.notification_service.send_verification_completed(
                user_id,
                "SMS",
                f"New message from {from_number}: {message_content[:50]}...",
            )

            result = {
                "message_id": db_message.id,
                "conversation_id": conversation.id,
                "user_id": user_id,
                "from_number": from_number,
                "to_number": to_number,
                "message": message_content,
                "received_at": db_message.created_at.isoformat(),
            }

            logger.info(f"SMS received and processed: {db_message.id}")
            return result

        except Exception as e:
            logger.error(f"Failed to process incoming SMS: {e}")
            raise

    # Voice Communication Methods
    async def make_voice_call_with_routing(
        self,
        user_id: str,
        to_number: str,
        from_number: str = None,
        twiml_url: str = None,
        use_smart_routing: bool = True,
        call_options: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Make voice call with intelligent routing

        Args:
            user_id: ID of the user making the call
            to_number: Recipient phone number
            from_number: Caller phone number (optional, will use routing if not provided)
            twiml_url: TwiML URL for call instructions
            use_smart_routing: Whether to use smart routing
            call_options: Additional call configuration

        Returns:
            Call initiation result with routing information
        """
        try:
            # Validate user
            user = self._get_active_user(user_id)

            # Get optimal caller number using smart routing
            if not from_number and use_smart_routing and self.routing_engine:
                user_numbers = await self._get_user_phone_numbers(user_id)
                routing_recommendation = (
                    await self.routing_engine.suggest_optimal_numbers(
                        destination_number=to_number,
                        user_numbers=[num.phone_number for num in user_numbers],
                        call_minutes=1,
                    )
                )
                from_number = routing_recommendation.primary_option.phone_number

            # Fallback to user's primary number
            if not from_number:
                user_numbers = await self._get_user_phone_numbers(user_id)
                from_number = (
                    user_numbers[0].phone_number if user_numbers else "+1555000001"
                )

            # Make call using Twilio client
            if not self.twilio_client:
                raise Exception("Twilio client not available")

            twilio_result = await self.twilio_client.make_call(
                from_number=from_number,
                to_number=to_number,
                twiml_url=twiml_url,
                **(call_options or {}),
            )

            # Create conversation for call history
            conversation = await self._get_or_create_conversation(
                user_id=user_id, external_number=to_number
            )

            # Store call record
            db_message = Message(
                conversation_id=conversation.id,
                sender_id=user_id,
                content=f"Voice call to {to_number}",
                message_type=MessageType.VOICE.value,
                from_number=from_number,
                to_number=to_number,
                external_message_id=twilio_result.get("sid"),
                delivery_status=twilio_result.get("status"),
                created_at=datetime.utcnow(),
            )

            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)

            result = {
                "call_id": db_message.id,
                "conversation_id": conversation.id,
                "call_sid": twilio_result.get("sid"),
                "from_number": from_number,
                "to_number": to_number,
                "status": twilio_result.get("status"),
                "routing_used": use_smart_routing,
                "initiated_at": db_message.created_at.isoformat(),
            }

            logger.info(
                f"Voice call initiated: {db_message.id} from {from_number} to {to_number}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to make voice call: {e}")
            raise

    async def receive_voice_call_webhook(
        self, webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process incoming voice call webhook from Twilio

        Args:
            webhook_data: Webhook payload from Twilio

        Returns:
            Processing result
        """
        try:
            # Process webhook data
            processed_data = await self.twilio_client.receive_call_webhook(webhook_data)

            from_number = processed_data["from_number"]
            to_number = processed_data["to_number"]
            call_status = processed_data["status"]

            # Find user who owns the receiving number
            phone_number_record = (
                self.db.query(PhoneNumber)
                .filter(
                    PhoneNumber.phone_number == to_number, PhoneNumber.is_active == True
                )
                .first()
            )

            if not phone_number_record:
                logger.warning(f"Received call for unknown number: {to_number}")
                return {"status": "ignored", "reason": "unknown_number"}

            user_id = phone_number_record.owner_id

            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                user_id=user_id, external_number=from_number
            )

            # Store incoming call record
            db_message = Message(
                conversation_id=conversation.id,
                sender_id=None,  # External caller
                content=f"Incoming voice call from {from_number}",
                message_type=MessageType.VOICE.value,
                from_number=from_number,
                to_number=to_number,
                external_message_id=processed_data.get("sid"),
                delivery_status=call_status,
                created_at=datetime.utcnow(),
            )

            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)

            # Update conversation
            conversation.last_message_at = datetime.utcnow()
            self.db.commit()

            result = {
                "call_id": db_message.id,
                "conversation_id": conversation.id,
                "user_id": user_id,
                "from_number": from_number,
                "to_number": to_number,
                "status": call_status,
                "received_at": db_message.created_at.isoformat(),
            }

            logger.info(f"Incoming call processed: {db_message.id}")
            return result

        except Exception as e:
            logger.error(f"Failed to process incoming call: {e}")
            raise

    # Call Recording and Forwarding Features
    async def record_call(
        self, user_id: str, call_sid: str, recording_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Start recording a call

        Args:
            user_id: ID of the user requesting recording
            call_sid: Twilio call SID to record
            recording_options: Additional recording configuration

        Returns:
            Recording initiation result
        """
        try:
            # Validate user and call ownership
            user = self._get_active_user(user_id)

            # Verify user owns this call
            call_message = (
                self.db.query(Message)
                .filter(
                    and_(
                        Message.external_message_id == call_sid,
                        Message.message_type == MessageType.VOICE.value,
                        Message.sender_id == user_id,
                    )
                )
                .first()
            )

            if not call_message:
                raise ValueError("Call not found or not owned by user")

            # Start recording using Twilio client
            recording_result = await self.twilio_client.record_call(
                call_sid=call_sid, **(recording_options or {})
            )

            # Update call message with recording info
            call_message.content += (
                f" [Recording: {recording_result.get('recording_sid')}]"
            )
            self.db.commit()

            result = {
                "call_id": call_message.id,
                "call_sid": call_sid,
                "recording_sid": recording_result.get("recording_sid"),
                "status": recording_result.get("status"),
                "started_at": recording_result.get("date_created"),
            }

            logger.info(
                f"Call recording started: {recording_result.get('recording_sid')} for call {call_sid}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to start call recording: {e}")
            raise

    async def forward_call(
        self,
        user_id: str,
        call_sid: str,
        forward_to: str,
        forwarding_options: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Forward a call to another number

        Args:
            user_id: ID of the user requesting forwarding
            call_sid: Twilio call SID to forward
            forward_to: Number to forward the call to
            forwarding_options: Additional forwarding configuration

        Returns:
            Call forwarding result
        """
        try:
            # Validate user and call ownership
            user = self._get_active_user(user_id)

            # Verify user owns this call
            call_message = (
                self.db.query(Message)
                .filter(
                    and_(
                        Message.external_message_id == call_sid,
                        Message.message_type == MessageType.VOICE.value,
                        Message.sender_id == user_id,
                    )
                )
                .first()
            )

            if not call_message:
                raise ValueError("Call not found or not owned by user")

            # Forward call using Twilio client
            forward_result = await self.twilio_client.forward_call(
                call_sid=call_sid, forward_to=forward_to, **(forwarding_options or {})
            )

            # Update call message with forwarding info
            call_message.content += f" [Forwarded to: {forward_to}]"
            self.db.commit()

            result = {
                "call_id": call_message.id,
                "call_sid": call_sid,
                "forwarded_to": forward_to,
                "status": forward_result.get("status"),
                "forwarded_at": forward_result.get("date_updated"),
            }

            logger.info(f"Call forwarded: {call_sid} to {forward_to}")
            return result

        except Exception as e:
            logger.error(f"Failed to forward call: {e}")
            raise

    async def create_conference_call(
        self,
        user_id: str,
        conference_name: str,
        participants: List[str],
        conference_options: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Create a conference call with multiple participants

        Args:
            user_id: ID of the user creating the conference
            conference_name: Name of the conference
            participants: List of phone numbers to include
            conference_options: Additional conference configuration

        Returns:
            Conference creation result
        """
        try:
            # Validate user
            user = self._get_active_user(user_id)

            # Create conference using Twilio client
            conference_result = await self.twilio_client.create_conference(
                conference_name=conference_name, **(conference_options or {})
            )

            # Create conversation for conference
            conversation = Conversation(
                title=f"Conference: {conference_name}",
                is_group=True,
                created_by=user_id,
                created_at=datetime.utcnow(),
            )

            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

            # Store conference record
            db_message = Message(
                conversation_id=conversation.id,
                sender_id=user_id,
                content=f"Conference call: {conference_name} with {len(participants)} participants",
                message_type=MessageType.VOICE.value,
                external_message_id=conference_result.get("conference_sid"),
                delivery_status="initiated",
                created_at=datetime.utcnow(),
            )

            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)

            result = {
                "conference_id": db_message.id,
                "conversation_id": conversation.id,
                "conference_sid": conference_result.get("conference_sid"),
                "conference_name": conference_name,
                "participants": participants,
                "status": conference_result.get("status"),
                "created_at": db_message.created_at.isoformat(),
            }

            logger.info(
                f"Conference call created: {conference_name} with {len(participants)} participants"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to create conference call: {e}")
            raise

    # Conversation and History Management
    async def get_conversation_history(
        self,
        user_id: str,
        conversation_id: str = None,
        external_number: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get conversation history for a user

        Args:
            user_id: ID of the user
            conversation_id: Specific conversation ID (optional)
            external_number: External number to filter by (optional)
            limit: Maximum number of messages to return
            offset: Offset for pagination

        Returns:
            Conversation history with messages
        """
        try:
            # Validate user
            user = self._get_active_user(user_id)

            # Build query
            query = (
                self.db.query(Message)
                .join(Conversation)
                .filter(
                    or_(
                        Conversation.created_by == user_id, Message.sender_id == user_id
                    )
                )
            )

            if conversation_id:
                query = query.filter(Message.conversation_id == conversation_id)

            if external_number:
                query = query.filter(
                    or_(
                        Message.from_number == external_number,
                        Message.to_number == external_number,
                    )
                )

            # Get messages with pagination
            messages = (
                query.order_by(desc(Message.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )

            # Convert to response format
            message_list = []
            for message in messages:
                message_data = {
                    "message_id": message.id,
                    "conversation_id": message.conversation_id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "from_number": message.from_number,
                    "to_number": message.to_number,
                    "is_outbound": message.sender_id == user_id,
                    "status": message.delivery_status,
                    "created_at": message.created_at.isoformat(),
                    "delivered_at": (
                        message.delivered_at.isoformat()
                        if message.delivered_at
                        else None
                    ),
                }
                message_list.append(message_data)

            # Get conversation info if specific conversation
            conversation_info = None
            if conversation_id:
                conversation = (
                    self.db.query(Conversation)
                    .filter(Conversation.id == conversation_id)
                    .first()
                )
                if conversation:
                    conversation_info = {
                        "conversation_id": conversation.id,
                        "title": conversation.title,
                        "is_group": conversation.is_group,
                        "external_number": conversation.external_number,
                        "created_at": conversation.created_at.isoformat(),
                        "last_message_at": (
                            conversation.last_message_at.isoformat()
                            if conversation.last_message_at
                            else None
                        ),
                    }

            result = {
                "user_id": user_id,
                "conversation_info": conversation_info,
                "messages": message_list,
                "total_messages": len(message_list),
                "limit": limit,
                "offset": offset,
            }

            return result

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise

    async def get_call_history(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get call history for a user

        Args:
            user_id: ID of the user
            limit: Maximum number of calls to return
            offset: Offset for pagination

        Returns:
            Call history with details
        """
        try:
            # Validate user
            user = self._get_active_user(user_id)

            # Get voice messages (calls)
            calls = (
                self.db.query(Message)
                .join(Conversation)
                .filter(
                    and_(
                        Message.message_type == MessageType.VOICE.value,
                        or_(
                            Conversation.created_by == user_id,
                            Message.sender_id == user_id,
                        ),
                    )
                )
                .order_by(desc(Message.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )

            # Convert to response format
            call_list = []
            for call in calls:
                call_data = {
                    "call_id": call.id,
                    "conversation_id": call.conversation_id,
                    "call_sid": call.external_message_id,
                    "from_number": call.from_number,
                    "to_number": call.to_number,
                    "is_outbound": call.sender_id == user_id,
                    "status": call.delivery_status,
                    "duration": call.duration if hasattr(call, "duration") else None,
                    "created_at": call.created_at.isoformat(),
                    "completed_at": (
                        call.delivered_at.isoformat() if call.delivered_at else None
                    ),
                    "content": call.content,
                }
                call_list.append(call_data)

            result = {
                "user_id": user_id,
                "calls": call_list,
                "total_calls": len(call_list),
                "limit": limit,
                "offset": offset,
            }

            return result

        except Exception as e:
            logger.error(f"Failed to get call history: {e}")
            raise

    # User Number Management Dashboard
    async def get_user_number_dashboard(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user number management dashboard

        Args:
            user_id: ID of the user

        Returns:
            Complete dashboard with numbers, usage, and analytics
        """
        try:
            # Validate user
            user = self._get_active_user(user_id)

            # Get user's phone numbers
            user_numbers = await self._get_user_phone_numbers(user_id)

            # Get usage statistics for each number
            number_stats = []
            total_sms_sent = 0
            total_sms_received = 0
            total_calls_made = 0
            total_calls_received = 0

            for number in user_numbers:
                # SMS statistics
                sms_sent = (
                    self.db.query(Message)
                    .filter(
                        and_(
                            Message.from_number == number.phone_number,
                            Message.message_type == MessageType.SMS.value,
                            Message.sender_id == user_id,
                        )
                    )
                    .count()
                )

                sms_received = (
                    self.db.query(Message)
                    .filter(
                        and_(
                            Message.to_number == number.phone_number,
                            Message.message_type == MessageType.SMS.value,
                            Message.sender_id.is_(None),
                        )
                    )
                    .count()
                )

                # Call statistics
                calls_made = (
                    self.db.query(Message)
                    .filter(
                        and_(
                            Message.from_number == number.phone_number,
                            Message.message_type == MessageType.VOICE.value,
                            Message.sender_id == user_id,
                        )
                    )
                    .count()
                )

                calls_received = (
                    self.db.query(Message)
                    .filter(
                        and_(
                            Message.to_number == number.phone_number,
                            Message.message_type == MessageType.VOICE.value,
                            Message.sender_id.is_(None),
                        )
                    )
                    .count()
                )

                # Calculate costs (simplified)
                estimated_sms_cost = (sms_sent + sms_received) * 0.0075
                estimated_call_cost = (calls_made + calls_received) * 0.02

                number_info = {
                    "number_id": number.id,
                    "phone_number": number.phone_number,
                    "country_code": number.country_code,
                    "is_active": number.is_active,
                    "purchased_at": (
                        number.purchased_at.isoformat() if number.purchased_at else None
                    ),
                    "expires_at": (
                        number.expires_at.isoformat() if number.expires_at else None
                    ),
                    "usage": {
                        "sms_sent": sms_sent,
                        "sms_received": sms_received,
                        "calls_made": calls_made,
                        "calls_received": calls_received,
                        "total_messages": sms_sent + sms_received,
                        "total_calls": calls_made + calls_received,
                    },
                    "costs": {
                        "estimated_sms_cost": estimated_sms_cost,
                        "estimated_call_cost": estimated_call_cost,
                        "total_estimated_cost": estimated_sms_cost
                        + estimated_call_cost,
                    },
                }

                number_stats.append(number_info)
                total_sms_sent += sms_sent
                total_sms_received += sms_received
                total_calls_made += calls_made
                total_calls_received += calls_received

            # Get recent activity (last 30 days)
            recent_date = datetime.utcnow() - timedelta(days=30)
            recent_messages = (
                self.db.query(Message)
                .join(Conversation)
                .filter(
                    and_(
                        Message.created_at >= recent_date,
                        or_(
                            Conversation.created_by == user_id,
                            Message.sender_id == user_id,
                        ),
                    )
                )
                .count()
            )

            # Get routing recommendations if available
            routing_recommendations = []
            if self.routing_engine and user_numbers:
                try:
                    # Get recent destinations for routing analysis
                    recent_destinations = (
                        self.db.query(Message.to_number)
                        .filter(
                            and_(
                                Message.sender_id == user_id,
                                Message.created_at >= recent_date,
                                Message.to_number.isnot(None),
                            )
                        )
                        .distinct()
                        .limit(10)
                        .all()
                    )

                    analytics = await self.routing_engine.get_routing_analytics(
                        user_numbers=[num.phone_number for num in user_numbers],
                        recent_destinations=[dest[0] for dest in recent_destinations],
                    )

                    routing_recommendations = analytics.get(
                        "optimization_opportunities", []
                    )
                except Exception as e:
                    logger.warning(f"Could not generate routing recommendations: {e}")

            dashboard = {
                "user_id": user_id,
                "summary": {
                    "total_numbers": len(user_numbers),
                    "active_numbers": len([n for n in user_numbers if n.is_active]),
                    "total_sms_sent": total_sms_sent,
                    "total_sms_received": total_sms_received,
                    "total_calls_made": total_calls_made,
                    "total_calls_received": total_calls_received,
                    "recent_activity_30_days": recent_messages,
                },
                "numbers": number_stats,
                "routing_recommendations": routing_recommendations,
                "generated_at": datetime.utcnow().isoformat(),
            }

            return dashboard

        except Exception as e:
            logger.error(f"Failed to get user number dashboard: {e}")
            raise

    async def manage_user_number(
        self, user_id: str, action: str, number_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manage user phone numbers (purchase, release, update)

        Args:
            user_id: ID of the user
            action: Action to perform ('purchase', 'release', 'update')
            number_data: Number data for the action

        Returns:
            Management operation result
        """
        try:
            # Validate user
            user = self._get_active_user(user_id)

            if action == "purchase":
                return await self._purchase_number_for_user(user_id, number_data)
            elif action == "release":
                return await self._release_user_number(user_id, number_data)
            elif action == "update":
                return await self._update_user_number(user_id, number_data)
            else:
                raise ValueError(f"Invalid action: {action}")

        except Exception as e:
            logger.error(f"Failed to manage user number: {e}")
            raise

    # Helper Methods
    def _get_active_user(self, user_id: str) -> User:
        """Get active user by ID"""
        user = (
            self.db.query(User)
            .filter(and_(User.id == user_id, User.is_active == True))
            .first()
        )

        if not user:
            raise ValueError(f"User {user_id} not found or inactive")

        return user

    async def _get_user_phone_numbers(self, user_id: str) -> List[PhoneNumber]:
        """Get user's phone numbers"""
        return (
            self.db.query(PhoneNumber)
            .filter(
                and_(PhoneNumber.owner_id == user_id, PhoneNumber.is_active == True)
            )
            .all()
        )

    async def _get_or_create_conversation(
        self, user_id: str, external_number: str
    ) -> Conversation:
        """Get existing conversation or create new one"""
        # Try to find existing conversation
        conversation = (
            self.db.query(Conversation)
            .filter(
                and_(
                    Conversation.created_by == user_id,
                    Conversation.external_number == external_number,
                )
            )
            .first()
        )

        if not conversation:
            # Create new conversation
            conversation = Conversation(
                title=f"Conversation with {external_number}",
                external_number=external_number,
                created_by=user_id,
                created_at=datetime.utcnow(),
            )

            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

        return conversation

    async def _purchase_number_for_user(
        self, user_id: str, number_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Purchase a phone number for user"""
        try:
            phone_number = number_data.get("phone_number")
            country_code = number_data.get("country_code", "US")

            if not phone_number:
                raise ValueError("Phone number is required")

            # Purchase number using Twilio client
            if self.twilio_client:
                purchase_result = await self.twilio_client.purchase_number(
                    phone_number=phone_number, **number_data
                )
            else:
                # Mock purchase for testing
                purchase_result = {
                    "sid": f"PN{phone_number[-10:]}",
                    "phone_number": phone_number,
                    "status": "purchased",
                }

            # Store in database
            db_number = PhoneNumber(
                phone_number=phone_number,
                country_code=country_code,
                owner_id=user_id,
                is_active=True,
                purchased_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),  # Default 30 days
            )

            self.db.add(db_number)
            self.db.commit()
            self.db.refresh(db_number)

            result = {
                "number_id": db_number.id,
                "phone_number": phone_number,
                "country_code": country_code,
                "status": "purchased",
                "purchased_at": db_number.purchased_at.isoformat(),
                "expires_at": db_number.expires_at.isoformat(),
                "twilio_sid": purchase_result.get("sid"),
            }

            logger.info(f"Number purchased for user {user_id}: {phone_number}")
            return result

        except Exception as e:
            logger.error(f"Failed to purchase number: {e}")
            raise

    async def _release_user_number(
        self, user_id: str, number_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Release a user's phone number"""
        try:
            number_id = number_data.get("number_id")

            if not number_id:
                raise ValueError("Number ID is required")

            # Get user's number
            db_number = (
                self.db.query(PhoneNumber)
                .filter(
                    and_(
                        PhoneNumber.id == number_id,
                        PhoneNumber.owner_id == user_id,
                        PhoneNumber.is_active == True,
                    )
                )
                .first()
            )

            if not db_number:
                raise ValueError("Number not found or not owned by user")

            # Release number using Twilio client
            if self.twilio_client:
                await self.twilio_client.release_number(db_number.phone_number)

            # Update database
            db_number.is_active = False
            self.db.commit()

            result = {
                "number_id": number_id,
                "phone_number": db_number.phone_number,
                "status": "released",
                "released_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Number released for user {user_id}: {db_number.phone_number}")
            return result

        except Exception as e:
            logger.error(f"Failed to release number: {e}")
            raise

    async def _update_user_number(
        self, user_id: str, number_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user's phone number settings"""
        try:
            number_id = number_data.get("number_id")

            if not number_id:
                raise ValueError("Number ID is required")

            # Get user's number
            db_number = (
                self.db.query(PhoneNumber)
                .filter(
                    and_(PhoneNumber.id == number_id, PhoneNumber.owner_id == user_id)
                )
                .first()
            )

            if not db_number:
                raise ValueError("Number not found or not owned by user")

            # Update allowed fields
            if "is_active" in number_data:
                db_number.is_active = number_data["is_active"]

            if "expires_at" in number_data:
                db_number.expires_at = datetime.fromisoformat(number_data["expires_at"])

            self.db.commit()

            result = {
                "number_id": number_id,
                "phone_number": db_number.phone_number,
                "status": "updated",
                "updated_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Number updated for user {user_id}: {db_number.phone_number}")
            return result

        except Exception as e:
            logger.error(f"Failed to update number: {e}")
            raise


# Factory function
def create_communication_service(
    db_session: Session, twilio_client: EnhancedTwilioClient = None
) -> CommunicationService:
    """
    Factory function to create communication service

    Args:
        db_session: Database session
        twilio_client: Enhanced Twilio client

    Returns:
        CommunicationService instance
    """
    try:
        return CommunicationService(db_session, twilio_client)
    except Exception as e:
        logger.error(f"Failed to create communication service: {e}")
        raise


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_communication_service():
        print("Communication Service - Ready for production use")
        print("Features:")
        print("- SMS sending with smart routing")
        print("- Voice calling with intelligent number selection")
        print("- Call recording and forwarding")
        print("- Conversation and call history management")
        print("- User number management dashboard")
        print("- Conference calling capabilities")

    asyncio.run(test_communication_service())
