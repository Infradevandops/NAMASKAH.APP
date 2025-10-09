#!/usr/bin/env python3
"""
AI Assistant API endpoints for namaskah Communication Platform
Provides API endpoints for AI assistance, contextual help, and intent analysis
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field, validator

from services.ai_assistant_service import (AIAssistantService,
                                           ConversationRole, IntentType,
                                           ResponseSuggestion)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

# Global AI service instance
ai_service = None


def get_ai_service() -> AIAssistantService:
    """Get AI Assistant service instance"""
    global ai_service
    if ai_service is None:
        ai_service = AIAssistantService()
    return ai_service


# Request/Response Models


class ConversationCreateRequest(BaseModel):
    """Request model for creating a conversation context"""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    participants: List[str] = Field(..., description="List of participant identifiers")
    initial_message: Optional[str] = Field(None, description="Optional initial message")

    @validator("conversation_id")
    def validate_conversation_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Conversation ID cannot be empty")
        return v.strip()

    @validator("participants")
    def validate_participants(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one participant is required")
        return v


class MessageAddRequest(BaseModel):
    """Request model for adding a message to conversation"""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional message metadata"
    )

    @validator("role")
    def validate_role(cls, v):
        valid_roles = [role.value for role in ConversationRole]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {valid_roles}")
        return v

    @validator("content")
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Message content cannot be empty")
        return v.strip()


class IntentAnalysisRequest(BaseModel):
    """Request model for message intent analysis"""

    message: str = Field(..., description="Message to analyze")

    @validator("message")
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Message cannot be empty")
        return v.strip()


class ResponseSuggestionsRequest(BaseModel):
    """Request model for response suggestions"""

    conversation_id: str = Field(..., description="Conversation identifier")
    incoming_message: str = Field(..., description="Incoming message to respond to")
    num_suggestions: int = Field(
        3, ge=1, le=10, description="Number of suggestions to generate"
    )

    @validator("conversation_id")
    def validate_conversation_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Conversation ID cannot be empty")
        return v.strip()

    @validator("incoming_message")
    def validate_incoming_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Incoming message cannot be empty")
        return v.strip()


class ContextualHelpRequest(BaseModel):
    """Request model for contextual help"""

    query: str = Field(..., description="User query for help")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Optional context information"
    )

    @validator("query")
    def validate_query(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Query cannot be empty")
        return v.strip()


class ConversationEnhancementRequest(BaseModel):
    """Request model for conversation enhancement"""

    conversation_id: str = Field(..., description="Conversation identifier")
    enhancement_type: str = Field(
        "auto",
        description="Type of enhancement (auto, summary, sentiment, topics, actions)",
    )

    @validator("conversation_id")
    def validate_conversation_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Conversation ID cannot be empty")
        return v.strip()

    @validator("enhancement_type")
    def validate_enhancement_type(cls, v):
        valid_types = ["auto", "summary", "sentiment", "topics", "actions"]
        if v not in valid_types:
            raise ValueError(f"Enhancement type must be one of: {valid_types}")
        return v


# Response Models


class ConversationContextResponse(BaseModel):
    """Response model for conversation context"""

    conversation_id: str
    participants: List[str]
    message_count: int
    created_at: datetime
    updated_at: datetime
    topic: Optional[str] = None
    language: str = "en"


class MessageResponse(BaseModel):
    """Response model for conversation messages"""

    role: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class IntentAnalysisResponse(BaseModel):
    """Response model for intent analysis"""

    message: str
    intent: str
    confidence: float
    analysis_timestamp: datetime


class ResponseSuggestionResponse(BaseModel):
    """Response model for individual response suggestion"""

    text: str
    confidence: float
    intent: str
    tone: str
    reasoning: str
    alternatives: Optional[List[str]] = None


class ResponseSuggestionsResponse(BaseModel):
    """Response model for response suggestions"""

    conversation_id: str
    incoming_message: str
    suggestions: List[ResponseSuggestionResponse]
    generated_at: datetime


class ContextualHelpResponse(BaseModel):
    """Response model for contextual help"""

    query: str
    intent: str
    confidence: float
    suggestions: List[str]
    resources: List[Dict[str, str]]
    quick_actions: List[str]
    generated_at: datetime


class ConversationEnhancementResponse(BaseModel):
    """Response model for conversation enhancement"""

    conversation_id: str
    enhancement_type: str
    enhancements: Dict[str, Any]
    generated_at: datetime


class HealthCheckResponse(BaseModel):
    """Response model for health check"""

    status: str
    model_loaded: bool
    active_conversations: int
    timestamp: datetime


# API Endpoints


@router.post("/conversations", response_model=ConversationContextResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    ai_service: AIAssistantService = Depends(get_ai_service),
):
    """
    Create a new conversation context for AI assistance

    Args:
        request: Conversation creation request
        ai_service: AI Assistant service instance

    Returns:
        ConversationContextResponse: Created conversation context
    """
    try:
        context = await ai_service.create_conversation_context(
            conversation_id=request.conversation_id,
            participants=request.participants,
            initial_message=request.initial_message,
        )

        return ConversationContextResponse(
            conversation_id=context.conversation_id,
            participants=context.participants,
            message_count=len(context.messages),
            created_at=context.created_at,
            updated_at=context.updated_at,
            topic=context.topic,
            language=context.language,
        )

    except ValueError as e:
        logger.warning(f"Invalid conversation creation request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create conversation context"
        )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationContextResponse,
)
async def add_message_to_conversation(
    conversation_id: str,
    request: MessageAddRequest,
    ai_service: AIAssistantService = Depends(get_ai_service),
):
    """
    Add a message to an existing conversation context

    Args:
        conversation_id: Conversation identifier
        request: Message addition request
        ai_service: AI Assistant service instance

    Returns:
        ConversationContextResponse: Updated conversation context
    """
    try:
        role = ConversationRole(request.role)

        context = await ai_service.add_message_to_context(
            conversation_id=conversation_id,
            role=role,
            content=request.content,
            metadata=request.metadata,
        )

        return ConversationContextResponse(
            conversation_id=context.conversation_id,
            participants=context.participants,
            message_count=len(context.messages),
            created_at=context.created_at,
            updated_at=context.updated_at,
            topic=context.topic,
            language=context.language,
        )

    except ValueError as e:
        logger.warning(f"Invalid message addition request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add message to conversation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to add message to conversation"
        )


@router.get(
    "/conversations/{conversation_id}/messages", response_model=List[MessageResponse]
)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    ai_service: AIAssistantService = Depends(get_ai_service),
):
    """
    Get messages from a conversation context

    Args:
        conversation_id: Conversation identifier
        limit: Maximum number of messages to return
        ai_service: AI Assistant service instance

    Returns:
        List[MessageResponse]: List of conversation messages
    """
    try:
        if conversation_id not in ai_service.conversation_contexts:
            raise HTTPException(status_code=404, detail="Conversation not found")

        context = ai_service.conversation_contexts[conversation_id]
        messages = context.messages[-limit:] if limit > 0 else context.messages

        return [
            MessageResponse(
                role=msg.role.value,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata,
            )
            for msg in messages
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation messages: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve conversation messages"
        )


@router.post("/analyze-intent", response_model=IntentAnalysisResponse)
async def analyze_message_intent(
    request: IntentAnalysisRequest,
    ai_service: AIAssistantService = Depends(get_ai_service),
):
    """
    Analyze the intent of a message

    Args:
        request: Intent analysis request
        ai_service: AI Assistant service instance

    Returns:
        IntentAnalysisResponse: Intent analysis results
    """
    try:
        intent, confidence = await ai_service.analyze_message_intent(request.message)

        return IntentAnalysisResponse(
            message=request.message,
            intent=intent.value,
            confidence=confidence,
            analysis_timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to analyze message intent: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze message intent")


@router.post("/suggest-responses", response_model=ResponseSuggestionsResponse)
async def generate_response_suggestions(
    request: ResponseSuggestionsRequest,
    background_tasks: BackgroundTasks,
    ai_service: AIAssistantService = Depends(get_ai_service),
):
    """
    Generate AI-powered response suggestions for a message

    Args:
        request: Response suggestions request
        background_tasks: Background tasks for async processing
        ai_service: AI Assistant service instance

    Returns:
        ResponseSuggestionsResponse: Generated response suggestions
    """
    try:
        suggestions = await ai_service.generate_response_suggestions(
            conversation_id=request.conversation_id,
            incoming_message=request.incoming_message,
            num_suggestions=request.num_suggestions,
        )

        suggestion_responses = [
            ResponseSuggestionResponse(
                text=suggestion.text,
                confidence=suggestion.confidence,
                intent=suggestion.intent.value,
                tone=suggestion.tone,
                reasoning=suggestion.reasoning,
                alternatives=suggestion.alternatives,
            )
            for suggestion in suggestions
        ]

        # Add background task to log suggestion usage
        background_tasks.add_task(
            log_suggestion_usage, request.conversation_id, len(suggestions)
        )

        return ResponseSuggestionsResponse(
            conversation_id=request.conversation_id,
            incoming_message=request.incoming_message,
            suggestions=suggestion_responses,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to generate response suggestions: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate response suggestions"
        )


@router.post("/contextual-help", response_model=ContextualHelpResponse)
async def provide_contextual_help(
    request: ContextualHelpRequest,
    ai_service: AIAssistantService = Depends(get_ai_service),
):
    """
    Provide contextual help and assistance for user queries

    Args:
        request: Contextual help request
        ai_service: AI Assistant service instance

    Returns:
        ContextualHelpResponse: Contextual help and suggestions
    """
    try:
        help_response = await ai_service.provide_contextual_help(
            query=request.query, context=request.context
        )

        return ContextualHelpResponse(
            query=request.query,
            intent=help_response["intent"].value,
            confidence=help_response["confidence"],
            suggestions=help_response["suggestions"],
            resources=help_response["resources"],
            quick_actions=help_response["quick_actions"],
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to provide contextual help: {e}")
        raise HTTPException(status_code=500, detail="Failed to provide contextual help")


@router.post("/enhance-conversation", response_model=ConversationEnhancementResponse)
async def enhance_conversation(
    request: ConversationEnhancementRequest,
    ai_service: AIAssistantService = Depends(get_ai_service),
):
    """
    Enhance conversation with AI-powered analysis and insights

    Args:
        request: Conversation enhancement request
        ai_service: AI Assistant service instance

    Returns:
        ConversationEnhancementResponse: Conversation enhancements
    """
    try:
        enhancements = await ai_service.enhance_conversation(
            conversation_id=request.conversation_id,
            enhancement_type=request.enhancement_type,
        )

        return ConversationEnhancementResponse(
            conversation_id=request.conversation_id,
            enhancement_type=request.enhancement_type,
            enhancements=enhancements,
            generated_at=datetime.utcnow(),
        )

    except ValueError as e:
        logger.warning(f"Invalid conversation enhancement request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to enhance conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to enhance conversation")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(ai_service: AIAssistantService = Depends(get_ai_service)):
    """
    Check the health status of the AI Assistant service

    Args:
        ai_service: AI Assistant service instance

    Returns:
        HealthCheckResponse: Service health status
    """
    try:
        model_loaded = (
            hasattr(ai_service, "local_model") and ai_service.local_model is not None
        )
        active_conversations = len(ai_service.conversation_contexts)

        return HealthCheckResponse(
            status="healthy" if model_loaded else "degraded",
            model_loaded=model_loaded,
            active_conversations=active_conversations,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            model_loaded=False,
            active_conversations=0,
            timestamp=datetime.utcnow(),
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str, ai_service: AIAssistantService = Depends(get_ai_service)
):
    """
    Delete a conversation context

    Args:
        conversation_id: Conversation identifier
        ai_service: AI Assistant service instance

    Returns:
        Dict: Deletion confirmation
    """
    try:
        if conversation_id not in ai_service.conversation_contexts:
            raise HTTPException(status_code=404, detail="Conversation not found")

        del ai_service.conversation_contexts[conversation_id]

        logger.info(f"Deleted conversation context: {conversation_id}")

        return {
            "message": "Conversation deleted successfully",
            "conversation_id": conversation_id,
            "deleted_at": datetime.utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


@router.get("/conversations", response_model=List[ConversationContextResponse])
async def list_conversations(
    limit: int = 100, ai_service: AIAssistantService = Depends(get_ai_service)
):
    """
    List all active conversation contexts

    Args:
        limit: Maximum number of conversations to return
        ai_service: AI Assistant service instance

    Returns:
        List[ConversationContextResponse]: List of conversation contexts
    """
    try:
        conversations = []

        for context in list(ai_service.conversation_contexts.values())[:limit]:
            conversations.append(
                ConversationContextResponse(
                    conversation_id=context.conversation_id,
                    participants=context.participants,
                    message_count=len(context.messages),
                    created_at=context.created_at,
                    updated_at=context.updated_at,
                    topic=context.topic,
                    language=context.language,
                )
            )

        return conversations

    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")


# Background Tasks


async def log_suggestion_usage(conversation_id: str, suggestion_count: int):
    """
    Log AI suggestion usage for analytics

    Args:
        conversation_id: Conversation identifier
        suggestion_count: Number of suggestions generated
    """
    try:
        logger.info(
            f"AI suggestions generated - Conversation: {conversation_id}, Count: {suggestion_count}"
        )
        # In production, this would log to analytics database

    except Exception as e:
        logger.error(f"Failed to log suggestion usage: {e}")


# Export router
__all__ = ["router"]
