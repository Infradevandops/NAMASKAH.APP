#!/usr/bin/env python3
"""
Messaging Service for namaskah Communication Platform
Handles both internal messaging and SMS to external numbers
"""
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from clients.mock_twilio_client import MockTwilioClient
from models.database import (Contact, Conversation, ConversationParticipant,
                             Message, MessageStatus, MessageType, NumberStatus,
                             PhoneNumber, User)


class MessagingService:
    """Comprehensive messaging service for internal and external communication"""

    def __init__(self, db_session: Session, sms_client):
        self.db = db_session
        self.sms_client = sms_client
        self.active_connections: Dict[str, Any] = {}  # WebSocket connections

    async def send_internal_message(
        self, sender_id: str, recipient_id: str, content: str
    ) -> Dict[str, Any]:
        """Send message between platform users"""
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation([sender_id, recipient_id])

            # Create message
            message = Message(
                conversation_id=conversation.id,
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                message_type=MessageType.INTERNAL,
                status=MessageStatus.SENT,
            )

            self.db.add(message)
            self.db.commit()

            # Send real-time notification
            await self._notify_users(
                [recipient_id],
                {
                    "type": "new_message",
                    "message": self._serialize_message(message),
                    "conversation_id": conversation.id,
                },
            )

            return {
                "success": True,
                "message_id": message.id,
                "conversation_id": conversation.id,
                "status": "sent",
            }

        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    async def send_sms_to_external(
        self,
        sender_id: str,
        phone_number: str,
        content: str,
        from_number_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send SMS to external phone number using purchased number"""
        try:
            # Get user's available numbers
            if from_number_id:
                from_number = (
                    self.db.query(PhoneNumber)
                    .filter(
                        and_(
                            PhoneNumber.id == from_number_id,
                            PhoneNumber.owner_id == sender_id,
                        )
                    )
                    .first()
                )
            else:
                # Use first available number
                from_number = (
                    self.db.query(PhoneNumber)
                    .filter(
                        and_(
                            PhoneNumber.owner_id == sender_id,
                            PhoneNumber.status == NumberStatus.ACTIVE,
                        )
                    )
                    .first()
                )

            if not from_number:
                return {"success": False, "error": "No available phone number"}

            # Get or create conversation with external number
            conversation = self._get_or_create_external_conversation(
                sender_id, phone_number
            )

            # Send SMS via provider
            sms_result = self.sms_client.messages.create(
                body=content, from_=from_number.phone_number, to=phone_number
            )

            # Create message record
            message = Message(
                conversation_id=conversation.id,
                sender_id=sender_id,
                content=content,
                message_type=MessageType.SMS_OUTBOUND,
                phone_number_id=from_number.id,
                external_number=phone_number,
                status=MessageStatus.SENT,
                provider_message_id=sms_result.sid,
            )

            self.db.add(message)

            # Update usage
            self._update_usage(
                sender_id, from_number.id, sms_sent=1, cost=from_number.sms_cost
            )

            self.db.commit()

            # Real-time update for sender
            await self._notify_users(
                [sender_id],
                {
                    "type": "sms_sent",
                    "message": self._serialize_message(message),
                    "conversation_id": conversation.id,
                },
            )

            return {
                "success": True,
                "message_id": message.id,
                "conversation_id": conversation.id,
                "provider_message_id": sms_result.sid,
                "cost": from_number.sms_cost,
                "from_number": from_number.phone_number,
            }

        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    async def handle_incoming_sms(
        self, from_number: str, to_number: str, content: str, provider_message_id: str
    ) -> Dict[str, Any]:
        """Handle incoming SMS from external number"""
        try:
            # Find which user owns the receiving number
            phone_number = (
                self.db.query(PhoneNumber)
                .filter(PhoneNumber.phone_number == to_number)
                .first()
            )

            if not phone_number or not phone_number.owner:
                return {"success": False, "error": "Number not found or not owned"}

            # Get or create conversation
            conversation = self._get_or_create_external_conversation(
                phone_number.owner_id, from_number
            )

            # Create message record
            message = Message(
                conversation_id=conversation.id,
                recipient_id=phone_number.owner_id,
                content=content,
                message_type=MessageType.SMS_INBOUND,
                phone_number_id=phone_number.id,
                external_number=from_number,
                status=MessageStatus.DELIVERED,
                provider_message_id=provider_message_id,
            )

            self.db.add(message)

            # Update usage
            self._update_usage(phone_number.owner_id, phone_number.id, sms_received=1)

            self.db.commit()

            # Real-time notification
            await self._notify_users(
                [phone_number.owner_id],
                {
                    "type": "sms_received",
                    "message": self._serialize_message(message),
                    "conversation_id": conversation.id,
                    "from_number": from_number,
                },
            )

            return {
                "success": True,
                "message_id": message.id,
                "conversation_id": conversation.id,
                "recipient_id": phone_number.owner_id,
            }

        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def get_user_conversations(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all conversations for a user"""
        conversations = (
            self.db.query(Conversation)
            .join(ConversationParticipant)
            .filter(ConversationParticipant.user_id == user_id)
            .order_by(Conversation.last_message_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for conv in conversations:
            # Get last message
            last_message = (
                self.db.query(Message)
                .filter(Message.conversation_id == conv.id)
                .order_by(Message.created_at.desc())
                .first()
            )

            # Get other participants
            participants = (
                self.db.query(User)
                .join(ConversationParticipant)
                .filter(
                    and_(
                        ConversationParticipant.conversation_id == conv.id,
                        ConversationParticipant.user_id != user_id,
                    )
                )
                .all()
            )

            # Get unread count
            participant = (
                self.db.query(ConversationParticipant)
                .filter(
                    and_(
                        ConversationParticipant.conversation_id == conv.id,
                        ConversationParticipant.user_id == user_id,
                    )
                )
                .first()
            )

            unread_count = (
                self.db.query(Message)
                .filter(
                    and_(
                        Message.conversation_id == conv.id,
                        Message.created_at > participant.last_read_at,
                        Message.sender_id != user_id,
                    )
                )
                .count()
            )

            result.append(
                {
                    "id": conv.id,
                    "name": conv.name
                    or self._get_conversation_name(conv, participants),
                    "is_group": conv.is_group,
                    "external_number": conv.external_number,
                    "participants": [self._serialize_user(p) for p in participants],
                    "last_message": (
                        self._serialize_message(last_message) if last_message else None
                    ),
                    "unread_count": unread_count,
                    "updated_at": conv.updated_at.isoformat(),
                }
            )

        return result

    def get_conversation_messages(
        self, conversation_id: str, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation"""
        # Verify user is participant
        participant = (
            self.db.query(ConversationParticipant)
            .filter(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
            .first()
        )

        if not participant:
            return []

        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Mark as read
        participant.last_read_at = datetime.utcnow()
        self.db.commit()

        return [self._serialize_message(msg) for msg in reversed(messages)]

    def search_messages(
        self, user_id: str, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search messages for a user"""
        # Get user's conversations
        user_conversations = (
            self.db.query(ConversationParticipant.conversation_id)
            .filter(ConversationParticipant.user_id == user_id)
            .subquery()
        )

        messages = (
            self.db.query(Message)
            .filter(
                and_(
                    Message.conversation_id.in_(user_conversations),
                    Message.content.contains(query),
                )
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )

        return [self._serialize_message(msg) for msg in messages]

    def get_user_contacts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's contacts"""
        contacts = self.db.query(Contact).filter(Contact.user_id == user_id).all()

        result = []
        for contact in contacts:
            contact_data = {
                "id": contact.id,
                "name": contact.name,
                "phone_number": contact.phone_number,
                "email": contact.email,
                "notes": contact.notes,
                "is_platform_user": contact.is_platform_user,
            }

            # If platform user, get their info
            if contact.is_platform_user and contact.platform_user_id:
                platform_user = (
                    self.db.query(User)
                    .filter(User.id == contact.platform_user_id)
                    .first()
                )
                if platform_user:
                    contact_data["platform_user"] = self._serialize_user(platform_user)

            result.append(contact_data)

        return result

    # Helper methods
    def _get_or_create_conversation(self, user_ids: List[str]) -> Conversation:
        """Get or create conversation between users"""
        if len(user_ids) == 2:
            # Direct conversation
            existing = (
                self.db.query(Conversation)
                .join(ConversationParticipant)
                .filter(
                    and_(
                        Conversation.is_group == False,
                        Conversation.external_number.is_(None),
                    )
                )
                .group_by(Conversation.id)
                .having(
                    self.db.query(ConversationParticipant.user_id)
                    .filter(ConversationParticipant.conversation_id == Conversation.id)
                    .filter(ConversationParticipant.user_id.in_(user_ids))
                    .count()
                    == len(user_ids)
                )
                .first()
            )

            if existing:
                return existing

        # Create new conversation
        conversation = Conversation(is_group=len(user_ids) > 2)
        self.db.add(conversation)
        self.db.flush()

        # Add participants
        for user_id in user_ids:
            participant = ConversationParticipant(
                conversation_id=conversation.id, user_id=user_id
            )
            self.db.add(participant)

        return conversation

    def _get_or_create_external_conversation(
        self, user_id: str, external_number: str
    ) -> Conversation:
        """Get or create conversation with external number"""
        existing = (
            self.db.query(Conversation)
            .filter(
                and_(
                    Conversation.external_number == external_number,
                    Conversation.participants.any(
                        ConversationParticipant.user_id == user_id
                    ),
                )
            )
            .first()
        )

        if existing:
            return existing

        # Create new external conversation
        conversation = Conversation(external_number=external_number, is_group=False)
        self.db.add(conversation)
        self.db.flush()

        # Add user as participant
        participant = ConversationParticipant(
            conversation_id=conversation.id, user_id=user_id
        )
        self.db.add(participant)

        return conversation

    def _update_usage(
        self,
        user_id: str,
        phone_number_id: str,
        sms_sent: int = 0,
        sms_received: int = 0,
        cost: float = 0.0,
    ):
        """Update usage statistics"""
        from models.database import Usage

        today = datetime.utcnow().date()
        usage = (
            self.db.query(Usage)
            .filter(
                and_(
                    Usage.user_id == user_id,
                    Usage.phone_number_id == phone_number_id,
                    Usage.date >= today,
                )
            )
            .first()
        )

        if not usage:
            usage = Usage(
                user_id=user_id, phone_number_id=phone_number_id, date=datetime.utcnow()
            )
            self.db.add(usage)

        usage.sms_sent += sms_sent
        usage.sms_received += sms_received
        usage.cost += cost

    def _serialize_message(self, message: Message) -> Dict[str, Any]:
        """Serialize message to dict"""
        if not message:
            return None

        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "content": message.content,
            "message_type": message.message_type.value,
            "status": message.status.value,
            "external_number": message.external_number,
            "phone_number_id": message.phone_number_id,
            "provider_message_id": message.provider_message_id,
            "is_edited": message.is_edited,
            "created_at": message.created_at.isoformat(),
            "updated_at": message.updated_at.isoformat(),
        }

    def _serialize_user(self, user: User) -> Dict[str, Any]:
        """Serialize user to dict"""
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
        }

    def _get_conversation_name(
        self, conversation: Conversation, participants: List[User]
    ) -> str:
        """Generate conversation name"""
        if conversation.external_number:
            return f"SMS: {conversation.external_number}"
        elif len(participants) == 1:
            return participants[0].display_name or participants[0].username
        else:
            names = [p.display_name or p.username for p in participants[:3]]
            if len(participants) > 3:
                names.append(f"and {len(participants) - 3} others")
            return ", ".join(names)

    async def _notify_users(self, user_ids: List[str], data: Dict[str, Any]):
        """Send real-time notifications to users"""
        # This would integrate with WebSocket connections
        for user_id in user_ids:
            if user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_json(data)
                except:
                    # Connection closed, remove it
                    del self.active_connections[user_id]
