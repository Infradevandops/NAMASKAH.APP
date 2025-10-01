#!/usr/bin/env python3
"""
Models package initialization
"""
from models.conversation_models import (Conversation, ConversationCreate,
                                        ConversationFilters,
                                        ConversationListResponse,
                                        ConversationResponse,
                                        ConversationStatus, ConversationUpdate,
                                        Message, MessageCreate, MessageFilters,
                                        MessageListResponse, MessageResponse,
                                        MessageType, MessageUpdate,
                                        conversation_participants)
from models.phone_number_models import PhoneNumber
# Import all models using the same Base
# Import Base first to ensure single registry
from models.user_models import APIKey, Base
from models.user_models import Session as UserSession
from models.user_models import (SubscriptionPlan, User, UserCreate,
                                UserResponse, UserRole)
from models.verification_models import VerificationRequest
from models.tenant_models import Tenant, TenantUser, TenantSettings, TenantInvitation, TenantContext
from models.rbac_models import Role, Permission, RolePermission, UserRole as RBACUserRole
from models.call_models import Call, WebRTCSession
from models.routing_models import RoutingRule, RoutingHistory, ConversationIntelligence

__all__ = [
    # Base
    "Base",
    # User models
    "User",
    "UserSession",
    "APIKey",
    "VerificationRequest",
    "PhoneNumber",
    "UserRole",
    "SubscriptionPlan",
    "UserCreate",
    "UserResponse",
    # Conversation models
    "Conversation",
    "Message",
    "conversation_participants",
    "ConversationStatus",
    "MessageType",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "MessageCreate",
    "MessageUpdate",
    "MessageResponse",
    "ConversationListResponse",
    "MessageListResponse",
    "ConversationFilters",
    "MessageFilters",
    # Tenant models
    "Tenant",
    "TenantUser",
    "TenantSettings",
    "TenantInvitation",
    "TenantContext",
    # RBAC models
    "Role",
    "Permission",
    "RolePermission",
    "RBACUserRole",
    # Call models
    "Call",
    "WebRTCSession",
    # Routing models
    "RoutingRule",
    "RoutingHistory",
    "ConversationIntelligence",
]
