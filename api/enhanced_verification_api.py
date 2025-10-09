#!/usr/bin/env python3
"""
Enhanced Verification API Endpoints for namaskah Communication Platform
Provides comprehensive REST API for verification management with integrated services,
smart routing, and advanced features
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException, Path,
                     Query)
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from auth.jwt_handler import verify_jwt_token
from core.database import get_db
from clients.enhanced_twilio_client import create_enhanced_twilio_client
from models.user_models import User
from services.integrated_verification_service import \
    IntegratedVerificationService
from clients.textverified_client import TextVerifiedClient

logger = logging.getLogger(__name__)

# Initialize router and security
router = APIRouter(prefix="/api/verification", tags=["Enhanced Verification"])
security = HTTPBearer()

# Request/Response Models


class VerificationCreateRequest(BaseModel):
    """Request model for creating a verification"""

    service_name: str = Field(
        ..., description="Service to verify (e.g., whatsapp, google)"
    )
    capability: str = Field("sms", description="Verification capability (sms, voice)")
    country_preference: Optional[str] = Field(
        None, description="Preferred country code for number"
    )
    use_smart_routing: bool = Field(
        True, description="Enable smart routing for optimal delivery"
    )
    priority: str = Field(
        "normal", description="Verification priority (low, normal, high)"
    )

    @validator("service_name")
    def validate_service_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Service name cannot be empty")
        return v.lower().strip()

    @validator("priority")
    def validate_priority(cls, v):
        valid_priorities = ["low", "normal", "high"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v


class VerificationResponse(BaseModel):
    """Response model for verification details"""

    id: str
    user_id: str
    service_name: str
    service_display_name: str
    phone_number: Optional[str]
    country_code: Optional[str]
    status: str
    verification_code: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    estimated_delivery_time: Optional[int]
    success_probability: Optional[float]
    cost_estimate: Optional[float]
    routing_info: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]


class VerificationListResponse(BaseModel):
    """Response model for verification list"""

    verifications: List[VerificationResponse]
    total_count: int
    page: int
    page_size: int
    filters_applied: Dict[str, Any]


class VerificationMessagesResponse(BaseModel):
    """Response model for verification messages"""

    verification_id: str
    messages: List[Dict[str, Any]]
    extracted_codes: List[str]
    auto_completed: bool
    last_checked: datetime
    next_check_in: Optional[int]


class VerificationStatsResponse(BaseModel):
    """Response model for verification statistics"""

    period_days: int
    total_verifications: int
    completed_verifications: int
    success_rate: float
    average_completion_time: Optional[float]
    status_breakdown: Dict[str, int]
    service_breakdown: Dict[str, int]
    country_breakdown: Dict[str, int]
    cost_summary: Dict[str, float]


class ServiceInfoResponse(BaseModel):
    """Response model for service information"""

    service_name: str
    display_name: str
    category: str
    typical_code_length: int
    average_delivery_time: int
    success_rate: float
    cost_tier: str
    supported_countries: List[str]
    features: List[str]


class VerificationBulkRequest(BaseModel):
    """Request model for bulk verification creation"""

    services: List[str] = Field(..., description="List of services to verify")
    capability: str = Field("sms", description="Verification capability")
    country_preference: Optional[str] = Field(
        None, description="Preferred country code"
    )
    use_smart_routing: bool = Field(True, description="Enable smart routing")
    stagger_delay: int = Field(
        5, ge=0, le=60, description="Delay between verifications in seconds"
    )


class VerificationRetryRequest(BaseModel):
    """Request model for retrying verification"""

    use_different_number: bool = Field(
        False, description="Use a different phone number"
    )
    country_preference: Optional[str] = Field(
        None, description="New country preference"
    )


# Dependencies


async def get_current_user(
    token: str = Depends(security), db: Session = Depends(get_db)
) -> User:
    """Extract and validate user from JWT token"""
    try:
        payload = verify_jwt_token(token.credentials)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        return user
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication")


def get_verification_service(
    db: Session = Depends(get_db),
) -> IntegratedVerificationService:
    """Get integrated verification service instance"""
    api_key = os.getenv("TEXTVERIFIED_API_KEY", "testkey")
    email = os.getenv("TEXTVERIFIED_EMAIL", "test@example.com")
    textverified_client = TextVerifiedClient(api_key, email)
    twilio_client = create_enhanced_twilio_client()
    return IntegratedVerificationService(db, textverified_client, twilio_client)


# API Endpoints


@router.post("/create", response_model=VerificationResponse)
async def create_verification(
    request: VerificationCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Create a new verification request with smart routing and optimization

    Args:
        request: Verification creation request
        background_tasks: Background tasks for async processing
        current_user: Authenticated user
        verification_service: Integrated verification service

    Returns:
        VerificationResponse: Created verification details
    """
    try:
        # Create verification with integrated service
        verification = await verification_service.create_service_verification(
            user_id=current_user.id,
            service_name=request.service_name,
            capability=request.capability,
            preferred_country=request.country_preference,
        )

        # Add background task for monitoring
        background_tasks.add_task(
            monitor_verification_progress, verification.id, current_user.id
        )

        # Convert to response format
        return await _convert_to_verification_response(
            verification, verification_service
        )

    except ValueError as e:
        logger.warning(f"Invalid verification request: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create verification: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create verification request"
        )


@router.get("", response_model=VerificationListResponse)
async def list_verifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    search: Optional[str] = Query(None, description="Search query"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    List verification requests with advanced filtering and search

    Args:
        page: Page number for pagination
        page_size: Number of items per page
        service_name: Filter by service name
        status: Filter by verification status
        country_code: Filter by country code
        date_from: Filter from date
        date_to: Filter to date
        search: Search query
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        current_user: Authenticated user
        verification_service: Integrated verification service

    Returns:
        VerificationListResponse: Paginated list of verifications
    """
    try:
        # Build filters
        filters = {
            "service_name": service_name,
            "status": status,
            "country_code": country_code,
            "date_from": date_from,
            "date_to": date_to,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        # Get verifications
        result = await verification_service.get_user_verification_history(
            user_id=current_user.id, filters=filters
        )

        # Convert to response format
        verification_responses = []
        for verification in result["verifications"]:
            response = await _convert_to_verification_response(
                verification, verification_service
            )
            verification_responses.append(response)

        return VerificationListResponse(
            verifications=verification_responses,
            total_count=result["total_count"],
            page=page,
            page_size=page_size,
            filters_applied=filters,
        )

    except Exception as e:
        logger.error(f"Failed to list verifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve verifications")


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification(
    verification_id: str = Path(..., description="Verification ID"),
    current_user: User = Depends(get_current_user),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Get detailed information about a specific verification

    Args:
        verification_id: Verification identifier
        current_user: Authenticated user
        verification_service: Integrated verification service

    Returns:
        VerificationResponse: Verification details
    """
    try:
        verification = await verification_service.get_verification_details(
            user_id=current_user.id, verification_id=verification_id
        )

        return await _convert_to_verification_response(
            verification, verification_service
        )

    except ValueError as e:
        logger.warning(f"Verification not found: {e}")
        raise HTTPException(status_code=404, detail="Verification not found")
    except Exception as e:
        logger.error(f"Failed to get verification: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve verification")


@router.get("/{verification_id}/messages", response_model=VerificationMessagesResponse)
async def get_verification_messages(
    verification_id: str = Path(..., description="Verification ID"),
    force_refresh: bool = Query(False, description="Force refresh from provider"),
    current_user: User = Depends(get_current_user),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Get SMS messages and extracted codes for a verification

    Args:
        verification_id: Verification identifier
        force_refresh: Force refresh from provider
        current_user: Authenticated user
        verification_service: Integrated verification service

    Returns:
        VerificationMessagesResponse: Messages and extracted codes
    """
    try:
        result = await verification_service.get_verification_messages(
            user_id=current_user.id,
            verification_id=verification_id,
            force_refresh=force_refresh,
        )

        return VerificationMessagesResponse(
            verification_id=verification_id,
            messages=result["messages"],
            extracted_codes=result["extracted_codes"],
            auto_completed=result["auto_completed"],
            last_checked=result["last_checked"],
            next_check_in=result.get("next_check_in"),
        )

    except ValueError as e:
        logger.warning(f"Verification not found: {e}")
        raise HTTPException(status_code=404, detail="Verification not found")
    except Exception as e:
        logger.error(f"Failed to get verification messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@router.post("/{verification_id}/retry", response_model=VerificationResponse)
async def retry_verification(
    request: VerificationRetryRequest,
    background_tasks: BackgroundTasks,
    verification_id: str = Path(..., description="Verification ID"),
    current_user: User = Depends(get_current_user),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Retry a failed or expired verification

    Args:
        verification_id: Verification identifier
        request: Retry request parameters
        background_tasks: Background tasks for async processing
        current_user: Authenticated user
        verification_service: Integrated verification service

    Returns:
        VerificationResponse: Updated verification details
    """
    try:
        verification = await verification_service.retry_verification(
            user_id=current_user.id,
            verification_id=verification_id,
            use_different_number=request.use_different_number,
            country_preference=request.country_preference,
        )

        # Add background task for monitoring
        background_tasks.add_task(
            monitor_verification_progress, verification.id, current_user.id
        )

        return await _convert_to_verification_response(
            verification, verification_service
        )

    except ValueError as e:
        logger.warning(f"Cannot retry verification: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to retry verification: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry verification")


@router.delete("/{verification_id}")
async def cancel_verification(
    verification_id: str = Path(..., description="Verification ID"),
    current_user: User = Depends(get_current_user),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Cancel an active verification request

    Args:
        verification_id: Verification identifier
        current_user: Authenticated user
        verification_service: Integrated verification service

    Returns:
        Dict: Cancellation confirmation
    """
    try:
        success = await verification_service.cancel_verification(
            user_id=current_user.id, verification_id=verification_id
        )

        if success:
            return {
                "message": "Verification cancelled successfully",
                "verification_id": verification_id,
                "cancelled_at": datetime.utcnow(),
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel verification")

    except ValueError as e:
        logger.warning(f"Cannot cancel verification: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel verification: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel verification")


@router.post("/bulk", response_model=List[VerificationResponse])
async def create_bulk_verifications(
    request: VerificationBulkRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Create multiple verification requests in bulk

    Args:
        request: Bulk verification request
        background_tasks: Background tasks for async processing
        current_user: Authenticated user
        verification_service: Integrated verification service

    Returns:
        List[VerificationResponse]: Created verifications
    """
    try:
        verifications = await verification_service.create_bulk_verifications(
            user_id=current_user.id,
            services=request.services,
            capability=request.capability,
            country_preference=request.country_preference,
            use_smart_routing=request.use_smart_routing,
            stagger_delay=request.stagger_delay,
        )

        # Add background tasks for monitoring
        for verification in verifications:
            background_tasks.add_task(
                monitor_verification_progress, verification.id, current_user.id
            )

        # Convert to response format
        responses = []
        for verification in verifications:
            response = await _convert_to_verification_response(
                verification, verification_service
            )
            responses.append(response)

        return responses

    except ValueError as e:
        logger.warning(f"Invalid bulk verification request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create bulk verifications: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create bulk verifications"
        )


@router.get("/services/supported", response_model=List[ServiceInfoResponse])
async def get_supported_services(
    category: Optional[str] = Query(None, description="Filter by service category"),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Get list of supported verification services

    Args:
        category: Filter by service category
        verification_service: Integrated verification service

    Returns:
        List[ServiceInfoResponse]: Supported services information
    """
    try:
        services = await verification_service.get_supported_services(category=category)

        return [
            ServiceInfoResponse(
                service_name=service["name"].lower(),
                display_name=service["display_name"],
                category=service["category"],
                typical_code_length=service["typical_code_length"],
                average_delivery_time=service["average_delivery_time"],
                success_rate=service["success_rate"],
                cost_tier=service["cost_tier"],
                supported_countries=service.get("supported_countries", []),
                features=service.get("features", []),
            )
            for service in services
        ]

    except Exception as e:
        logger.error(f"Failed to get supported services: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve supported services"
        )


@router.get("/stats/summary", response_model=VerificationStatsResponse)
async def get_verification_statistics(
    period_days: int = Query(30, ge=1, le=365, description="Statistics period in days"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    current_user: User = Depends(get_current_user),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Get comprehensive verification statistics

    Args:
        period_days: Statistics period in days
        service_name: Filter by service name
        current_user: Authenticated user
        verification_service: Integrated verification service

    Returns:
        VerificationStatsResponse: Verification statistics
    """
    try:
        stats = await verification_service.get_verification_analytics(
            user_id=current_user.id,
            period_days=period_days,
            service_filter=service_name,
        )

        return VerificationStatsResponse(
            period_days=stats["period_days"],
            total_verifications=stats["total_verifications"],
            completed_verifications=stats["completed_verifications"],
            success_rate=stats["success_rate"],
            average_completion_time=stats.get("average_completion_time"),
            status_breakdown=stats["status_breakdown"],
            service_breakdown=stats["service_breakdown"],
            country_breakdown=stats.get("country_breakdown", {}),
            cost_summary=stats.get("cost_summary", {}),
        )

    except Exception as e:
        logger.error(f"Failed to get verification statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/export/data")
async def export_verification_data(
    format_type: str = Query("json", regex="^(json|csv)$", description="Export format"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_user),
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Export verification data in various formats

    Args:
        format_type: Export format (json, csv)
        service_name: Filter by service name
        status: Filter by status
        date_from: Filter from date
        date_to: Filter to date
        current_user: Authenticated user
        verification_service: Integrated verification service

    Returns:
        Exported data in requested format
    """
    try:
        # Build filters
        filters = {
            "service_name": service_name,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        # Export data
        export_result = await verification_service.export_verification_data(
            user_id=current_user.id, format_type=format_type, filters=filters
        )

        if format_type == "csv":
            return Response(
                content=export_result["content"],
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=verifications_{current_user.id}_{datetime.now().strftime('%Y%m%d')}.csv"
                },
            )
        else:
            return export_result

    except Exception as e:
        logger.error(f"Failed to export verification data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data")


@router.get("/health")
async def health_check(
    verification_service: IntegratedVerificationService = Depends(
        get_verification_service
    ),
):
    """
    Check the health status of the verification service

    Args:
        verification_service: Integrated verification service

    Returns:
        Dict: Service health status
    """
    try:
        health_status = await verification_service.check_service_health()

        return {
            "status": "healthy" if health_status["overall_healthy"] else "degraded",
            "timestamp": datetime.utcnow(),
            "components": health_status["components"],
            "active_verifications": health_status.get("active_verifications", 0),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "timestamp": datetime.utcnow(), "error": str(e)}


# Helper Functions


async def _convert_to_verification_response(
    verification: Any, verification_service: IntegratedVerificationService
) -> VerificationResponse:
    """
    Convert verification object to response format

    Args:
        verification: Verification object
        verification_service: Verification service for additional data

    Returns:
        VerificationResponse: Formatted response
    """
    try:
        # Get additional metadata
        service_info = await verification_service.get_service_info(
            verification.service_name
        )
        routing_info = getattr(verification, "routing_info", None)

        return VerificationResponse(
            id=verification.id,
            user_id=verification.user_id,
            service_name=verification.service_name,
            service_display_name=service_info.get(
                "display_name", verification.service_name.title()
            ),
            phone_number=verification.phone_number,
            country_code=getattr(verification, "country_code", None),
            status=verification.status,
            verification_code=verification.verification_code,
            created_at=verification.created_at,
            updated_at=verification.updated_at,
            completed_at=getattr(verification, "completed_at", None),
            expires_at=getattr(verification, "expires_at", None),
            estimated_delivery_time=service_info.get("average_delivery_time"),
            success_probability=service_info.get("success_rate"),
            cost_estimate=getattr(verification, "cost_estimate", None),
            routing_info=routing_info,
            metadata=getattr(verification, "metadata", {}),
        )

    except Exception as e:
        logger.warning(f"Failed to convert verification response: {e}")
        # Return basic response if conversion fails
        return VerificationResponse(
            id=verification.id,
            user_id=verification.user_id,
            service_name=verification.service_name,
            service_display_name=verification.service_name.title(),
            phone_number=verification.phone_number,
            country_code=None,
            status=verification.status,
            verification_code=verification.verification_code,
            created_at=verification.created_at,
            updated_at=verification.updated_at,
            completed_at=None,
            expires_at=None,
            estimated_delivery_time=None,
            success_probability=None,
            cost_estimate=None,
            routing_info=None,
            metadata={},
        )


# Background Tasks


async def monitor_verification_progress(verification_id: str, user_id: str):
    """
    Background task to monitor verification progress

    Args:
        verification_id: Verification identifier
        user_id: User identifier
    """
    try:
        logger.info(f"Starting verification monitoring for {verification_id}")

        # In production, this would:
        # 1. Periodically check verification status
        # 2. Send notifications on completion
        # 3. Handle timeouts and retries
        # 4. Update analytics

        await asyncio.sleep(1)  # Placeholder for actual monitoring logic

        logger.info(f"Verification monitoring completed for {verification_id}")

    except Exception as e:
        logger.error(f"Verification monitoring failed for {verification_id}: {e}")


# Export router
__all__ = ["router"]
