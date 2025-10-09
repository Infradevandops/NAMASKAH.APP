#!/usr/bin/env python3
"""
Conversation API endpoints for namaskah Platform
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from models import (Conversation, ConversationCreate, ConversationFilters,
                    ConversationListResponse, ConversationResponse,
                    ConversationStatus, ConversationUpdate, Message,
                    MessageCreate, MessageFilters, MessageListResponse,
                    MessageResponse, MessageType, MessageUpdate, User)
from services.auth_service import get_current_active_user
from services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

# Conversation endpoints


@router.get("/", response_model=ConversationListResponse)
async def get_user_conversations(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[ConversationStatus] = Query(None),
    is_group: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get conversations for the current user with filtering
    """
    try:
        conversation_service = ConversationService(db)

        # Build filters
        filters = ConversationFilters(
            status=status, is_group=is_group, is_archived=is_archived
        )

        # Get conversations
        conversations, total_count = await conversation_service.get_user_conversations(
            current_user.id, filters=filters, limit=limit, offset=offset
        )

        # Get unread count
        unread_total = await conversation_service.get_unread_count(current_user.id)

        # Convert to response format
        conversation_responses = []
        for conv in conversations:
            # Count unread messages in this conversation
            unread_count = 0
            for msg in conv.messages:
                if msg.sender_id != current_user.id and not msg.is_read:
                    unread_count += 1

            conversation_responses.append(
                ConversationResponse(
                    id=conv.id,
                    title=conv.title,
                    is_group=conv.is_group,
                    external_number=conv.external_number,
                    status=conv.status,
                    created_by=conv.created_by,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    last_message_at=conv.last_message_at,
                    is_archived=conv.is_archived,
                    is_muted=conv.is_muted,
                    participant_count=len(conv.participants),
                    unread_count=unread_count,
                )
            )

        return ConversationListResponse(
            conversations=conversation_responses,
            total_count=total_count,
            unread_total=unread_total,
        )

    except Exception as e:
        logger.error(f"Error getting conversations for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversations",
        )


@router.post(
    "/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new conversation
    """
    try:
        conversation_service = ConversationService(db)

        # Create conversation
        conversation = await conversation_service.create_conversation(
            current_user.id, conversation_data
        )

        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            is_group=conversation.is_group,
            external_number=conversation.external_number,
            status=conversation.status,
            created_by=conversation.created_by,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            last_message_at=conversation.last_message_at,
            is_archived=conversation.is_archived,
            is_muted=conversation.is_muted,
            participant_count=len(conversation.participants),
            unread_count=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific conversation by ID
    """
    try:
        conversation_service = ConversationService(db)

        conversation = await conversation_service.get_conversation(
            conversation_id, current_user.id
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        # Count unread messages
        unread_count = 0
        for msg in conversation.messages:
            if msg.sender_id != current_user.id and not msg.is_read:
                unread_count += 1

        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            is_group=conversation.is_group,
            external_number=conversation.external_number,
            status=conversation.status,
            created_by=conversation.created_by,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            last_message_at=conversation.last_message_at,
            is_archived=conversation.is_archived,
            is_muted=conversation.is_muted,
            participant_count=len(conversation.participants),
            unread_count=unread_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation",
        )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update conversation settings
    """
    try:
        conversation_service = ConversationService(db)

        conversation = await conversation_service.update_conversation(
            conversation_id, current_user.id, update_data
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            is_group=conversation.is_group,
            external_number=conversation.external_number,
            status=conversation.status,
            created_by=conversation.created_by,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            last_message_at=conversation.last_message_at,
            is_archived=conversation.is_archived,
            is_muted=conversation.is_muted,
            participant_count=len(conversation.participants),
            unread_count=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation",
        )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete conversation (soft delete)
    """
    try:
        conversation_service = ConversationService(db)

        result = await conversation_service.delete_conversation(
            conversation_id, current_user.id
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied",
            )

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )


# Participant management endpoints


@router.post("/{conversation_id}/participants")
async def add_participants(
    conversation_id: str,
    participant_ids: List[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Add participants to conversation
    """
    try:
        conversation_service = ConversationService(db)

        result = await conversation_service.add_participants(
            conversation_id, current_user.id, participant_ids
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add participants",
            )

        return {"message": f"Added {len(participant_ids)} participants successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding participants to {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add participants",
        )


@router.delete("/{conversation_id}/participants/{participant_id}")
async def remove_participant(
    conversation_id: str,
    participant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Remove participant from conversation
    """
    try:
        conversation_service = ConversationService(db)

        result = await conversation_service.remove_participant(
            conversation_id, current_user.id, participant_id
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found or access denied",
            )

        return {"message": "Participant removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing participant from {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove participant",
        )


# Message endpoints


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    before_message_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get messages from a conversation with pagination
    """
    try:
        conversation_service = ConversationService(db)

        messages, total_count = await conversation_service.get_conversation_messages(
            conversation_id,
            current_user.id,
            limit=limit,
            offset=offset,
            before_message_id=before_message_id,
        )

        # Convert to response format
        message_responses = []
        for msg in messages:
            message_responses.append(
                MessageResponse(
                    id=msg.id,
                    conversation_id=msg.conversation_id,
                    sender_id=msg.sender_id,
                    content=msg.content,
                    message_type=msg.message_type,
                    external_message_id=msg.external_message_id,
                    from_number=msg.from_number,
                    to_number=msg.to_number,
                    is_delivered=msg.is_delivered,
                    is_read=msg.is_read,
                    delivery_status=msg.delivery_status,
                    is_edited=msg.is_edited,
                    is_deleted=msg.is_deleted,
                    created_at=msg.created_at,
                    updated_at=msg.updated_at,
                    delivered_at=msg.delivered_at,
                    read_at=msg.read_at,
                    sender_username=msg.sender.username if msg.sender else None,
                )
            )

        has_more = (offset + limit) < total_count
        next_cursor = messages[-1].id if messages and has_more else None

        return MessageListResponse(
            messages=message_responses,
            total_count=total_count,
            has_more=has_more,
            next_cursor=next_cursor,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages",
        )


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to a conversation
    """
    try:
        conversation_service = ConversationService(db)

        message = await conversation_service.send_message(
            conversation_id, current_user.id, message_data
        )

        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            content=message.content,
            message_type=message.message_type,
            external_message_id=message.external_message_id,
            from_number=message.from_number,
            to_number=message.to_number,
            is_delivered=message.is_delivered,
            is_read=message.is_read,
            delivery_status=message.delivery_status,
            is_edited=message.is_edited,
            is_deleted=message.is_deleted,
            created_at=message.created_at,
            updated_at=message.updated_at,
            delivered_at=message.delivered_at,
            read_at=message.read_at,
            sender_username=current_user.username,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message",
        )


@router.put("/{conversation_id}/messages/{message_id}", response_model=MessageResponse)
async def update_message(
    conversation_id: str,
    message_id: str,
    update_data: MessageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update a message (only by sender)
    """
    try:
        conversation_service = ConversationService(db)

        message = await conversation_service.update_message(
            message_id, current_user.id, update_data
        )

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or access denied",
            )

        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            content=message.content,
            message_type=message.message_type,
            external_message_id=message.external_message_id,
            from_number=message.from_number,
            to_number=message.to_number,
            is_delivered=message.is_delivered,
            is_read=message.is_read,
            delivery_status=message.delivery_status,
            is_edited=message.is_edited,
            is_deleted=message.is_deleted,
            created_at=message.created_at,
            updated_at=message.updated_at,
            delivered_at=message.delivered_at,
            read_at=message.read_at,
            sender_username=current_user.username,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message",
        )


@router.delete("/{conversation_id}/messages/{message_id}")
async def delete_message(
    conversation_id: str,
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete a message (soft delete, only by sender)
    """
    try:
        conversation_service = ConversationService(db)

        result = await conversation_service.delete_message(message_id, current_user.id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or access denied",
            )

        return {"message": "Message deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message",
        )


# Utility endpoints


@router.post("/{conversation_id}/messages/mark-read")
async def mark_messages_as_read(
    conversation_id: str,
    up_to_message_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Mark messages as read in a conversation
    """
    try:
        conversation_service = ConversationService(db)

        marked_count = await conversation_service.mark_messages_as_read(
            conversation_id, current_user.id, up_to_message_id
        )

        return {
            "message": f"Marked {marked_count} messages as read",
            "marked_count": marked_count,
        }

    except Exception as e:
        logger.error(f"Error marking messages as read in {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark messages as read",
        )


@router.get("/search/messages", response_model=MessageListResponse)
async def search_messages(
    query: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    message_type: Optional[MessageType] = Query(None),
    sender_id: Optional[str] = Query(None),
    conversation_id: Optional[str] = Query(None),
    created_after: Optional[str] = Query(None),
    created_before: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Enhanced search messages across user's conversations with filtering
    """
    try:
        conversation_service = ConversationService(db)

        # Parse date filters
        from datetime import datetime

        parsed_after = None
        parsed_before = None

        if created_after:
            try:
                parsed_after = datetime.fromisoformat(
                    created_after.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid created_after date format. Use ISO format.",
                )

        if created_before:
            try:
                parsed_before = datetime.fromisoformat(
                    created_before.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid created_before date format. Use ISO format.",
                )

        # Build filters
        filters = MessageFilters(
            message_type=message_type,
            sender_id=sender_id,
            created_after=parsed_after,
            created_before=parsed_before,
        )

        # Add conversation filter if specified
        if conversation_id:
            filters.conversation_id = conversation_id

        messages, total_count = await conversation_service.search_messages(
            current_user.id, query, filters=filters, limit=limit, offset=offset
        )

        # Convert to response format
        message_responses = []
        for msg in messages:
            message_responses.append(
                MessageResponse(
                    id=msg.id,
                    conversation_id=msg.conversation_id,
                    sender_id=msg.sender_id,
                    content=msg.content,
                    message_type=msg.message_type,
                    external_message_id=msg.external_message_id,
                    from_number=msg.from_number,
                    to_number=msg.to_number,
                    is_delivered=msg.is_delivered,
                    is_read=msg.is_read,
                    delivery_status=msg.delivery_status,
                    is_edited=msg.is_edited,
                    is_deleted=msg.is_deleted,
                    created_at=msg.created_at,
                    updated_at=msg.updated_at,
                    delivered_at=msg.delivered_at,
                    read_at=msg.read_at,
                    sender_username=msg.sender.username if msg.sender else None,
                )
            )

        has_more = (offset + limit) < total_count

        return MessageListResponse(
            messages=message_responses, total_count=total_count, has_more=has_more
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching messages for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages",
        )


@router.get("/search/conversations")
async def search_conversations(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Search conversations by title or participant names
    """
    try:
        conversation_service = ConversationService(db)

        conversations, total_count = await conversation_service.search_conversations(
            current_user.id, query, limit=limit, offset=offset
        )

        # Convert to response format
        conversation_responses = []
        for conv in conversations:
            # Count unread messages in this conversation
            unread_count = 0
            for msg in conv.messages:
                if msg.sender_id != current_user.id and not msg.is_read:
                    unread_count += 1

            conversation_responses.append(
                ConversationResponse(
                    id=conv.id,
                    title=conv.title,
                    is_group=conv.is_group,
                    external_number=conv.external_number,
                    status=conv.status,
                    created_by=conv.created_by,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    last_message_at=conv.last_message_at,
                    is_archived=conv.is_archived,
                    is_muted=conv.is_muted,
                    participant_count=len(conv.participants),
                    unread_count=unread_count,
                )
            )

        has_more = (offset + limit) < total_count

        return {
            "conversations": conversation_responses,
            "total_count": total_count,
            "has_more": has_more,
        }

    except Exception as e:
        logger.error(f"Error searching conversations for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search conversations",
        )


@router.get("/mentions/users")
async def get_user_mentions(
    query: str = Query("", min_length=0),
    conversation_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get user suggestions for mentions and autocomplete
    """
    try:
        conversation_service = ConversationService(db)

        users = await conversation_service.get_user_mentions(
            current_user.id, query, conversation_id=conversation_id, limit=limit
        )

        return {"users": users, "query": query, "conversation_id": conversation_id}

    except Exception as e:
        logger.error(f"Error getting user mentions for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user mentions",
        )


# Health check
@router.get("/health")
async def conversation_health_check():
    """
    Health check for conversation service
    """
    return {
        "status": "healthy",
        "service": "conversations",
        "version": "1.1.0",
        "features": [
            "conversation_management",
            "message_persistence",
            "participant_management",
            "message_search",
            "read_receipts",
            "pagination",
        ],
    }
