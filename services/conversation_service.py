#!/usr/bin/env python3
"""
Conversation Management Service for namaskah Platform
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, asc, desc, func, or_, text
from sqlalchemy.orm import Session, joinedload

from models import (Conversation, ConversationCreate, ConversationFilters,
                    ConversationStatus, ConversationUpdate, Message,
                    MessageCreate, MessageFilters, MessageType, MessageUpdate,
                    User, conversation_participants)

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages"""

    def __init__(self, db: Session):
        self.db = db

    # Conversation CRUD Operations

    async def create_conversation(
        self, creator_id: str, conversation_data: ConversationCreate
    ) -> Conversation:
        """
        Create a new conversation with participants
        """
        try:
            # Validate creator exists
            creator = self.db.query(User).filter(User.id == creator_id).first()
            if not creator:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Creator not found"
                )

            # Validate participants exist
            participants = []
            if conversation_data.participant_ids:
                participants = (
                    self.db.query(User)
                    .filter(User.id.in_(conversation_data.participant_ids))
                    .all()
                )

                if len(participants) != len(conversation_data.participant_ids):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more participants not found",
                    )

            # Create conversation
            conversation = Conversation(
                title=conversation_data.title,
                is_group=conversation_data.is_group,
                external_number=conversation_data.external_number,
                created_by=creator_id,
                status=ConversationStatus.ACTIVE,
            )

            # Add creator as participant if not already included
            if creator not in participants:
                participants.append(creator)

            # Add participants
            conversation.participants.extend(participants)

            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

            logger.info(f"Conversation created: {conversation.id} by user {creator_id}")

            return conversation

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating conversation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create conversation",
            )

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID if user is a participant
        """
        try:
            conversation = (
                self.db.query(Conversation)
                .options(
                    joinedload(Conversation.participants),
                    joinedload(Conversation.creator),
                )
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.participants.any(User.id == user_id),
                )
                .first()
            )

            return conversation

        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None

    async def update_conversation(
        self, conversation_id: str, user_id: str, update_data: ConversationUpdate
    ) -> Optional[Conversation]:
        """
        Update conversation settings (only by participants)
        """
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

            # Update fields
            if update_data.title is not None:
                conversation.title = update_data.title
            if update_data.is_archived is not None:
                conversation.is_archived = update_data.is_archived
            if update_data.is_muted is not None:
                conversation.is_muted = update_data.is_muted
            if update_data.status is not None:
                conversation.status = update_data.status

            conversation.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(conversation)

            logger.info(f"Conversation updated: {conversation_id} by user {user_id}")

            return conversation

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating conversation {conversation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update conversation",
            )

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        Soft delete conversation (only by creator or admin)
        """
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

            # Check if user is creator or admin
            if conversation.created_by != user_id:
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user or user.role != "admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only conversation creator or admin can delete",
                    )

            conversation.status = ConversationStatus.DELETED
            conversation.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Conversation deleted: {conversation_id} by user {user_id}")

            return True

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False

    # Participant Management

    async def add_participants(
        self, conversation_id: str, user_id: str, participant_ids: List[str]
    ) -> bool:
        """
        Add participants to conversation
        """
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

            # Validate new participants exist
            new_participants = (
                self.db.query(User).filter(User.id.in_(participant_ids)).all()
            )

            if len(new_participants) != len(participant_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more participants not found",
                )

            # Add only new participants
            existing_ids = {p.id for p in conversation.participants}
            for participant in new_participants:
                if participant.id not in existing_ids:
                    conversation.participants.append(participant)

            conversation.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Participants added to conversation {conversation_id}")

            return True

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding participants to {conversation_id}: {e}")
            return False

    async def remove_participant(
        self, conversation_id: str, user_id: str, participant_id: str
    ) -> bool:
        """
        Remove participant from conversation
        """
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

            # Find participant to remove
            participant_to_remove = None
            for participant in conversation.participants:
                if participant.id == participant_id:
                    participant_to_remove = participant
                    break

            if not participant_to_remove:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Participant not found in conversation",
                )

            # Remove participant
            conversation.participants.remove(participant_to_remove)
            conversation.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(
                f"Participant {participant_id} removed from conversation {conversation_id}"
            )

            return True

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing participant from {conversation_id}: {e}")
            return False

    # Message Operations

    async def send_message(
        self, conversation_id: str, sender_id: str, message_data: MessageCreate
    ) -> Message:
        """
        Send a message to a conversation
        """
        try:
            # Validate conversation and sender access
            conversation = await self.get_conversation(conversation_id, sender_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

            # Create message
            message = Message(
                conversation_id=conversation_id,
                sender_id=sender_id,
                content=message_data.content,
                message_type=message_data.message_type,
                to_number=message_data.to_number,
            )

            # Handle SMS messages
            if message_data.message_type in [
                MessageType.SMS_OUTBOUND,
                MessageType.SMS_INBOUND,
            ]:
                if message_data.to_number:
                    message.to_number = message_data.to_number
                if conversation.external_number:
                    message.from_number = conversation.external_number

            self.db.add(message)

            # Update conversation last message time
            conversation.last_message_at = datetime.utcnow()
            conversation.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(message)

            logger.info(
                f"Message sent to conversation {conversation_id} by user {sender_id}"
            )

            return message

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error sending message to {conversation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message",
            )

    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        before_message_id: Optional[str] = None,
    ) -> Tuple[List[Message], int]:
        """
        Get messages from a conversation with pagination
        """
        try:
            # Validate access
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )

            # Build query
            query = (
                self.db.query(Message)
                .options(joinedload(Message.sender))
                .filter(
                    Message.conversation_id == conversation_id,
                    Message.is_deleted == False,
                )
            )

            # Handle cursor-based pagination
            if before_message_id:
                before_message = (
                    self.db.query(Message)
                    .filter(Message.id == before_message_id)
                    .first()
                )
                if before_message:
                    query = query.filter(Message.created_at < before_message.created_at)

            # Get total count
            total_count = query.count()

            # Apply pagination and ordering
            messages = (
                query.order_by(desc(Message.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )

            # Reverse to get chronological order
            messages.reverse()

            return messages, total_count

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error getting messages for conversation {conversation_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get messages",
            )

    async def update_message(
        self, message_id: str, user_id: str, update_data: MessageUpdate
    ) -> Optional[Message]:
        """
        Update a message (only by sender)
        """
        try:
            message = (
                self.db.query(Message)
                .filter(Message.id == message_id, Message.sender_id == user_id)
                .first()
            )

            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
                )

            # Update fields
            if update_data.content is not None:
                message.content = update_data.content
                message.is_edited = True

            if update_data.is_read is not None:
                message.is_read = update_data.is_read
                if update_data.is_read and not message.read_at:
                    message.read_at = datetime.utcnow()

            message.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(message)

            logger.info(f"Message updated: {message_id} by user {user_id}")

            return message

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating message {message_id}: {e}")
            return None

    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """
        Soft delete a message (only by sender)
        """
        try:
            message = (
                self.db.query(Message)
                .filter(Message.id == message_id, Message.sender_id == user_id)
                .first()
            )

            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
                )

            message.is_deleted = True
            message.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Message deleted: {message_id} by user {user_id}")

            return True

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting message {message_id}: {e}")
            return False

    # Search and Filtering

    async def get_user_conversations(
        self,
        user_id: str,
        filters: Optional[ConversationFilters] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Conversation], int]:
        """
        Get conversations for a user with filtering
        """
        try:
            # Base query
            query = (
                self.db.query(Conversation)
                .options(
                    joinedload(Conversation.participants),
                    joinedload(Conversation.creator),
                )
                .join(conversation_participants)
                .filter(conversation_participants.c.user_id == user_id)
            )

            # Apply filters
            if filters:
                if filters.status:
                    query = query.filter(Conversation.status == filters.status)
                if filters.is_group is not None:
                    query = query.filter(Conversation.is_group == filters.is_group)
                if filters.is_archived is not None:
                    query = query.filter(
                        Conversation.is_archived == filters.is_archived
                    )
                if filters.created_after:
                    query = query.filter(
                        Conversation.created_at >= filters.created_after
                    )
                if filters.created_before:
                    query = query.filter(
                        Conversation.created_at <= filters.created_before
                    )

            # Get total count
            total_count = query.count()

            # Apply pagination and ordering
            conversations = (
                query.order_by(desc(Conversation.last_message_at))
                .offset(offset)
                .limit(limit)
                .all()
            )

            return conversations, total_count

        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get conversations",
            )

    async def search_messages(
        self,
        user_id: str,
        query: str,
        filters: Optional[MessageFilters] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Message], int]:
        """
        Enhanced search messages across user's conversations with full-text capabilities
        """
        try:
            # Get user's conversation IDs
            user_conversations = (
                self.db.query(Conversation.id)
                .join(conversation_participants)
                .filter(conversation_participants.c.user_id == user_id)
                .subquery()
            )

            # Build enhanced search query with multiple search strategies
            search_query = (
                self.db.query(Message)
                .options(joinedload(Message.sender), joinedload(Message.conversation))
                .filter(
                    Message.conversation_id.in_(user_conversations),
                    Message.is_deleted == False,
                )
            )

            # Enhanced search with multiple conditions
            if query:
                # Split query into words for better matching
                words = query.strip().split()
                search_conditions = []

                # Exact phrase match (highest priority)
                search_conditions.append(Message.content.ilike(f"%{query}%"))

                # Individual word matches
                for word in words:
                    if len(word) >= 2:  # Skip very short words
                        search_conditions.append(Message.content.ilike(f"%{word}%"))

                # Combine search conditions with OR
                if search_conditions:
                    search_query = search_query.filter(or_(*search_conditions))

            # Apply filters
            if filters:
                if filters.message_type:
                    search_query = search_query.filter(
                        Message.message_type == filters.message_type
                    )
                if filters.sender_id:
                    search_query = search_query.filter(
                        Message.sender_id == filters.sender_id
                    )
                if filters.is_read is not None:
                    search_query = search_query.filter(
                        Message.is_read == filters.is_read
                    )
                if filters.created_after:
                    search_query = search_query.filter(
                        Message.created_at >= filters.created_after
                    )
                if filters.created_before:
                    search_query = search_query.filter(
                        Message.created_at <= filters.created_before
                    )
                if hasattr(filters, "conversation_id") and filters.conversation_id:
                    search_query = search_query.filter(
                        Message.conversation_id == filters.conversation_id
                    )

            # Get total count
            total_count = search_query.count()

            # Apply pagination and ordering with relevance scoring
            messages = (
                search_query.order_by(desc(Message.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )

            return messages, total_count

        except Exception as e:
            logger.error(f"Error searching messages for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search messages",
            )

    async def search_conversations(
        self, user_id: str, query: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[Conversation], int]:
        """
        Search conversations by title or participant names
        """
        try:
            # Base query for user's conversations
            search_query = (
                self.db.query(Conversation)
                .options(
                    joinedload(Conversation.participants),
                    joinedload(Conversation.creator),
                )
                .join(conversation_participants)
                .filter(
                    conversation_participants.c.user_id == user_id,
                    Conversation.status != ConversationStatus.DELETED,
                )
            )

            # Search by conversation title or participant usernames
            if query:
                words = query.strip().split()
                search_conditions = []

                # Search in conversation titles
                for word in words:
                    if len(word) >= 2:
                        search_conditions.append(Conversation.title.ilike(f"%{word}%"))

                # Search in participant usernames (requires subquery)
                participant_search = (
                    self.db.query(conversation_participants.c.conversation_id)
                    .join(User, conversation_participants.c.user_id == User.id)
                    .filter(
                        or_(
                            *[
                                User.username.ilike(f"%{word}%")
                                for word in words
                                if len(word) >= 2
                            ]
                        )
                    )
                    .subquery()
                )

                search_conditions.append(Conversation.id.in_(participant_search))

                if search_conditions:
                    search_query = search_query.filter(or_(*search_conditions))

            # Get total count
            total_count = search_query.count()

            # Apply pagination and ordering
            conversations = (
                search_query.order_by(desc(Conversation.last_message_at))
                .offset(offset)
                .limit(limit)
                .all()
            )

            return conversations, total_count

        except Exception as e:
            logger.error(f"Error searching conversations for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search conversations",
            )

    async def get_user_mentions(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get user suggestions for mentions/autocomplete
        """
        try:
            # Base query for users
            users_query = self.db.query(User).filter(
                User.id != user_id, User.is_active == True  # Exclude current user
            )

            # If conversation specified, prioritize conversation participants
            if conversation_id:
                # Get conversation participants first
                conversation = await self.get_conversation(conversation_id, user_id)
                if conversation:
                    participant_ids = [
                        p.id for p in conversation.participants if p.id != user_id
                    ]
                    if participant_ids:
                        # Prioritize conversation participants
                        participant_users = users_query.filter(
                            User.id.in_(participant_ids)
                        )
                        if query:
                            participant_users = participant_users.filter(
                                or_(
                                    User.username.ilike(f"%{query}%"),
                                    User.email.ilike(f"%{query}%"),
                                    func.concat(
                                        User.first_name, " ", User.last_name
                                    ).ilike(f"%{query}%"),
                                )
                            )

                        participants = participant_users.limit(limit).all()

                        # If we have enough participants, return them
                        if len(participants) >= limit:
                            return [
                                {
                                    "id": user.id,
                                    "username": user.username,
                                    "display_name": f"{user.first_name} {user.last_name}".strip()
                                    or user.username,
                                    "email": user.email,
                                    "is_participant": True,
                                }
                                for user in participants
                            ]

                        # Otherwise, get additional users to fill the limit
                        remaining_limit = limit - len(participants)
                        other_users_query = users_query.filter(
                            ~User.id.in_(participant_ids)
                        )
                        if query:
                            other_users_query = other_users_query.filter(
                                or_(
                                    User.username.ilike(f"%{query}%"),
                                    User.email.ilike(f"%{query}%"),
                                    func.concat(
                                        User.first_name, " ", User.last_name
                                    ).ilike(f"%{query}%"),
                                )
                            )

                        other_users = other_users_query.limit(remaining_limit).all()

                        # Combine results
                        all_users = participants + other_users
                        return [
                            {
                                "id": user.id,
                                "username": user.username,
                                "display_name": f"{user.first_name} {user.last_name}".strip()
                                or user.username,
                                "email": user.email,
                                "is_participant": user.id in participant_ids,
                            }
                            for user in all_users
                        ]

            # General user search
            if query:
                users_query = users_query.filter(
                    or_(
                        User.username.ilike(f"%{query}%"),
                        User.email.ilike(f"%{query}%"),
                        func.concat(User.first_name, " ", User.last_name).ilike(
                            f"%{query}%"
                        ),
                    )
                )

            users = users_query.limit(limit).all()

            return [
                {
                    "id": user.id,
                    "username": user.username,
                    "display_name": f"{user.first_name} {user.last_name}".strip()
                    or user.username,
                    "email": user.email,
                    "is_participant": False,
                }
                for user in users
            ]

        except Exception as e:
            logger.error(f"Error getting user mentions for user {user_id}: {e}")
            return []

    # Utility Methods

    async def mark_messages_as_read(
        self, conversation_id: str, user_id: str, up_to_message_id: Optional[str] = None
    ) -> int:
        """
        Mark messages as read in a conversation
        """
        try:
            # Validate access
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                return 0

            # Build query for unread messages
            query = self.db.query(Message).filter(
                Message.conversation_id == conversation_id,
                Message.sender_id != user_id,  # Don't mark own messages
                Message.is_read == False,
            )

            # Limit to messages up to a specific message
            if up_to_message_id:
                up_to_message = (
                    self.db.query(Message)
                    .filter(Message.id == up_to_message_id)
                    .first()
                )
                if up_to_message:
                    query = query.filter(Message.created_at <= up_to_message.created_at)

            # Update messages
            updated_count = query.update(
                {Message.is_read: True, Message.read_at: datetime.utcnow()}
            )

            self.db.commit()

            logger.info(
                f"Marked {updated_count} messages as read in conversation {conversation_id}"
            )

            return updated_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking messages as read in {conversation_id}: {e}")
            return 0

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get total unread message count for user
        """
        try:
            # Get user's conversation IDs
            user_conversations = (
                self.db.query(Conversation.id)
                .join(conversation_participants)
                .filter(conversation_participants.c.user_id == user_id)
                .subquery()
            )

            # Count unread messages
            unread_count = (
                self.db.query(Message)
                .filter(
                    Message.conversation_id.in_(user_conversations),
                    Message.sender_id != user_id,  # Don't count own messages
                    Message.is_read == False,
                    Message.is_deleted == False,
                )
                .count()
            )

            return unread_count

        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {e}")
            return 0
