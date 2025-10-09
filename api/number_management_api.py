#!/usr/bin/env python3
"""
Number Management API Endpoints for namaskah Communication Platform
Provides comprehensive phone number search, purchase, and management.
This is the unified API for all phone number operations.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException, Path,
                     Query)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from auth.jwt_handler import verify_jwt_token
from core.database import get_db
from clients.enhanced_twilio_client import (EnhancedTwilioClient,
                                    create_enhanced_twilio_client)
from models.phone_number_models import PhoneNumber as PhoneNumberModel
from models.user_models import User
from services.auth_service import get_current_active_user
from services.phone_number_service import PhoneNumberService
from services.smart_routing_engine import SmartRoutingEngine

logger = logging.getLogger(__name__)

# Initialize router and security
router = APIRouter(prefix="/api/numbers", tags=["Number Management"])
security = HTTPBearer()

# Request/Response Models


class NumberSearchRequest(BaseModel):
    """Request model for number search"""

    country_code: str = Field(..., description="Country code (e.g., US, CA, GB)")
    area_code: Optional[str] = Field(None, description="Area code preference")
    number_type: str = Field(
        "local", description="Number type (local, toll_free, mobile)"
    )
    capabilities: List[str] = Field(
        ["sms", "voice"], description="Required capabilities"
    )
    limit: int = Field(10, ge=1, le=50, description="Maximum numbers to return")
    contains: Optional[str] = Field(
        None, description="Number must contain these digits"
    )
    exclude_patterns: Optional[List[str]] = Field(
        None, description="Patterns to exclude"
    )

    @validator("country_code")
    def validate_country_code(cls, v):
        if not v or len(v) != 2:
            raise ValueError("Country code must be 2 characters (e.g., US, CA)")
        return v.upper()

    @validator("number_type")
    def validate_number_type(cls, v):
        valid_types = ["local", "toll_free", "mobile"]
        if v not in valid_types:
            raise ValueError(f"Number type must be one of: {valid_types}")
        return v

    @validator("capabilities")
    def validate_capabilities(cls, v):
        valid_capabilities = ["sms", "voice", "mms", "fax"]
        for cap in v:
            if cap not in valid_capabilities:
                raise ValueError(
                    f"Invalid capability: {cap}. Must be one of: {valid_capabilities}"
                )
        return v


class NumberPurchaseRequest(BaseModel):
    """Request model for number purchase"""

    phone_number: str = Field(..., description="Phone number to purchase")
    friendly_name: Optional[str] = Field(
        None, description="Webhook URL for incoming messages/calls"
    )

    @validator("phone_number")
    def validate_phone_number(cls, v):
        if not v or not v.startswith("+"):
            raise ValueError("Phone number must be in E.164 format (+1234567890)")
        return v


class NumberUpdateRequest(BaseModel):
    """Request model for number updates"""

    friendly_name: Optional[str] = Field(None, description="Update friendly name")
    auto_renew: Optional[bool] = Field(None, description="Update auto-renewal setting")
    usage_plan: Optional[str] = Field(None, description="Update usage plan")
    webhook_url: Optional[str] = Field(None, description="Update webhook URL")
    status: Optional[str] = Field(None, description="Update number status")

    @validator("usage_plan")
    def validate_usage_plan(cls, v):
        if v is not None:
            valid_plans = ["basic", "standard", "premium"]
            if v not in valid_plans:
                raise ValueError(f"Usage plan must be one of: {valid_plans}")
        return v

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["active", "inactive", "suspended"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class CostCalculationRequest(BaseModel):
    """Request model for cost calculation"""

    from_country: str = Field(..., description="Origin country code")
    to_country: str = Field(..., description="Destination country code")
    message_count: int = Field(1, ge=1, description="Number of messages")
    call_minutes: int = Field(0, ge=0, description="Call duration in minutes")
    number_type: str = Field("local", description="Number type for calculation")

    @validator("from_country", "to_country")
    def validate_country_codes(cls, v):
        if not v or len(v) != 2:
            raise ValueError("Country code must be 2 characters")
        return v.upper()


class NumberOptimizationRequest(BaseModel):
    """Request model for number optimization"""

    target_countries: List[str] = Field(
        ..., description="Target countries for optimization"
    )
    monthly_message_volume: int = Field(
        100, ge=1, description="Expected monthly message volume"
    )
    monthly_call_minutes: int = Field(
        60, ge=0, description="Expected monthly call minutes"
    )
    budget_limit: Optional[float] = Field(None, description="Monthly budget limit")
    optimization_goal: str = Field(
        "cost", description="Optimization goal (cost, delivery, coverage)"
    )

    @validator("target_countries")
    def validate_target_countries(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one target country is required")
        return [country.upper() for country in v]

    @validator("optimization_goal")
    def validate_optimization_goal(cls, v):
        valid_goals = ["cost", "delivery", "coverage"]
        if v not in valid_goals:
            raise ValueError(f"Optimization goal must be one of: {valid_goals}")
        return v


# Response Models


class AvailableNumberResponse(BaseModel):
    """Response model for available numbers"""

    phone_number: str
    friendly_name: str
    country_code: str
    area_code: Optional[str] = None
    number_type: Optional[str] = "local"
    capabilities: List[str]
    monthly_cost: Decimal
    setup_cost: Decimal = Decimal("0.0")
    locality: Optional[str] = None
    region: Optional[str] = None
    iso_country: Optional[str] = None
    beta: Optional[bool] = False
    provider: str = "twilio"
    sms_cost_per_message: Optional[Decimal] = None
    voice_cost_per_minute: Optional[Decimal] = None


class AvailableNumberListResponse(BaseModel):
    success: bool
    country_code: str
    area_code: Optional[str]
    total_count: int
    numbers: List[AvailableNumberResponse]


class PurchasedNumberResponse(BaseModel):
    """Response model for purchased numbers"""

    phone_number: str
    friendly_name: str
    country_code: str
    capabilities: List[str]
    status: str
    monthly_cost: Decimal
    usage_plan: Optional[str] = "standard"
    auto_renew: bool
    purchased_at: datetime
    next_billing_date: datetime
    webhook_url: Optional[str]
    id: str


class NumberUsageResponse(BaseModel):
    """Response model for number usage statistics"""

    phone_number: str
    period_start: datetime
    period_end: datetime
    messages_sent: int
    messages_received: int
    calls_made: int
    calls_received: int
    total_cost: float
    cost_breakdown: Dict[str, float]
    usage_by_country: Dict[str, int]


class CostEstimateResponse(BaseModel):
    """Response model for cost estimates"""

    from_country: str
    to_country: str
    message_cost: float
    call_cost_per_minute: float
    total_estimated_cost: float
    currency: str
    cost_breakdown: Dict[str, float]
    recommendations: List[str]


class OptimizationRecommendationResponse(BaseModel):
    """Response model for optimization recommendations"""

    current_setup: Dict[str, Any]
    recommended_setup: Dict[str, Any]
    potential_savings: float
    coverage_improvement: float
    delivery_improvement: float
    implementation_steps: List[str]
    cost_comparison: Dict[str, float]


class NumberAnalyticsResponse(BaseModel):
    """Response model for number analytics"""

    total_numbers: int
    active_numbers: int
    total_monthly_cost: float
    usage_efficiency: float
    top_performing_numbers: List[Dict[str, Any]]
    underutilized_numbers: List[Dict[str, Any]]
    cost_trends: Dict[str, List[float]]
    recommendations: List[str]


# Dependencies


def get_phone_number_service(
    db: Session = Depends(get_db),
    twilio_client: EnhancedTwilioClient = Depends(create_enhanced_twilio_client),
) -> PhoneNumberService:
    """
    Dependency to get phone number service instance.
    This now uses the real Twilio client.
    """
    return PhoneNumberService(
        db=db, twilio_client=twilio_client, textverified_client=None
    )


def get_twilio_client() -> EnhancedTwilioClient:
    """Get Enhanced Twilio client instance"""
    try:
        return create_enhanced_twilio_client()
    except Exception as e:
        logger.error(f"Failed to create Twilio client: {e}")
        raise HTTPException(status_code=503, detail="Twilio service unavailable")


def get_routing_engine(
    twilio_client: EnhancedTwilioClient = Depends(get_twilio_client),
) -> SmartRoutingEngine:
    """Get Smart Routing Engine instance"""
    try:
        return SmartRoutingEngine(twilio_client)
    except Exception as e:
        logger.error(f"Failed to create routing engine: {e}")
        raise HTTPException(status_code=503, detail="Routing service unavailable")


# API Endpoints


@router.get("/available/{country_code}", response_model=AvailableNumberListResponse)
async def search_available_numbers(
    country_code: str = Path(..., description="Country code (e.g., US, GB, CA)"),
    area_code: Optional[str] = Query(None, description="Area code filter"),
    capabilities: Optional[str] = Query(
        "sms,voice", description="Comma-separated capabilities (sms,voice,mms)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    current_user: User = Depends(get_current_active_user),
    phone_service: PhoneNumberService = Depends(get_phone_number_service),
):
    """
    Search for available phone numbers with filtering options
    """
    try:
        capability_list = (
            [cap.strip() for cap in capabilities.split(",")] if capabilities else []
        )

        numbers, total_count = await phone_service.search_available_numbers(
            country_code=country_code.upper(),
            area_code=area_code,
            capabilities=capability_list,
            limit=limit,
        )

        # Convert to response format
        response_numbers = [
            AvailableNumberResponse(
                phone_number=num["phone_number"],
                friendly_name=num["friendly_name"],
                country_code=num["country_code"],
                area_code=num.get("area_code"),
                number_type=num.get("number_type", "local"),
                capabilities=num["capabilities"],
                monthly_cost=Decimal(num["monthly_cost"]),
                setup_cost=Decimal(num.get("setup_cost", "0.0")),
                locality=num.get("locality"),
                region=num.get("region"),
                iso_country=num.get("iso_country"),
                beta=num.get("beta", False),
                provider=num.get("provider", "twilio"),
                sms_cost_per_message=Decimal(num.get("sms_cost_per_message", "0.0")),
                voice_cost_per_minute=Decimal(num.get("voice_cost_per_minute", "0.0")),
            )
            for num in numbers
        ]

        return AvailableNumberListResponse(
            success=True,
            country_code=country_code.upper(),
            area_code=area_code,
            total_count=total_count,
            numbers=response_numbers,
        )

    except ValueError as e:
        logger.warning(f"Invalid search request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to search numbers: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to search available numbers"
        )


@router.post("/purchase")
async def purchase_phone_number(
    request: NumberPurchaseRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    phone_service: PhoneNumberService = Depends(get_phone_number_service),
):
    """
    Purchase a phone number for the user
    """
    try:
        result = await phone_service.purchase_phone_number(
            user_id=current_user.id,
            phone_number=request.phone_number,
            auto_renew=True,  # Default to auto-renew
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400, detail=result.get("message", "Purchase failed")
            )

        purchased_number: PhoneNumberModel = result["phone_number"]

        return {
            "success": True,
            "message": result["message"],
            "transaction_id": result["transaction_id"],
            "phone_number": {
                "id": purchased_number.id,
                "phone_number": purchased_number.phone_number,
                "friendly_name": purchased_number.phone_number,
                "country_code": purchased_number.country_code,
                "capabilities": purchased_number.capabilities,
                "status": purchased_number.status,
                "monthly_cost": purchased_number.monthly_cost,
                "auto_renew": purchased_number.auto_renew,
                "purchased_at": purchased_number.purchased_at,
                "next_billing_date": purchased_number.expires_at,
            },
        }

    except ValueError as e:
        logger.warning(f"Invalid purchase request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to purchase number: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/owned", response_model=List[PurchasedNumberResponse])
async def get_owned_numbers(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    country_filter: Optional[str] = Query(None, description="Filter by country"),
    current_user: User = Depends(get_current_active_user),
    phone_service: PhoneNumberService = Depends(get_phone_number_service),
):
    """
    Get list of user's owned phone numbers

    Args:
        status_filter: Filter by number status
        country_filter: Filter by country code
        current_user: Authenticated user from dependency
        phone_service: Phone number service from dependency

    Returns:
        List[PurchasedNumberResponse]: Owned numbers
    """
    try:
        owned_numbers, total_count = await phone_service.get_owned_numbers(
            user_id=current_user.id, include_inactive=(status_filter == "inactive")
        )

        total_monthly_cost = sum(
            Decimal(num.monthly_cost or "0.0")
            for num in owned_numbers
            if num.status == "active"
        )

        return [
            PurchasedNumberResponse(
                phone_number=num["phone_number"],
                friendly_name=num["friendly_name"],
                country_code=num["country_code"],
                capabilities=num["capabilities"],
                status=num["status"],
                monthly_cost=Decimal(num["monthly_cost"]),
                usage_plan="standard",
                auto_renew=num["auto_renew"],
                purchased_at=num["purchased_at"],
                next_billing_date=num["expires_at"],
                id=num.id,
            )
            for num in owned_numbers
        ]

    except Exception as e:
        logger.error(f"Failed to get owned numbers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve owned numbers")


@router.put("/{phone_number}", response_model=PurchasedNumberResponse)
async def update_phone_number(
    request: NumberUpdateRequest,
    phone_number: str = Path(..., description="Phone number to update"),
    current_user: User = Depends(get_current_active_user),
    phone_service: PhoneNumberService = Depends(get_phone_number_service),
):
    """
    Update phone number settings

    Args:
        phone_number: Phone number to update
        request: Update request
        current_user: Authenticated user
        twilio_client: Enhanced Twilio client

    Returns:
        PurchasedNumberResponse: Updated number details
    """
    try:
        # Update the number
        updated_number = await twilio_client.update_phone_number(
            user_id=current_user.id,
            phone_number=phone_number,
            friendly_name=request.friendly_name,
            auto_renew=request.auto_renew,
            usage_plan=request.usage_plan,
            webhook_url=request.webhook_url,
            status=request.status,
        )

        return PurchasedNumberResponse(
            phone_number=updated_number["phone_number"],
            friendly_name=updated_number["friendly_name"],
            country_code=updated_number["country_code"],
            capabilities=updated_number["capabilities"],
            status=updated_number["status"],
            monthly_cost=Decimal(updated_number["monthly_cost"]),
            usage_plan="standard",
            auto_renew=updated_number["auto_renew"],
            purchased_at=updated_number["purchased_at"],
            next_billing_date=updated_number["expires_at"],
            id=updated_number.id,
        )

    except ValueError as e:
        logger.warning(f"Invalid update request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update number: {e}")
        raise HTTPException(status_code=500, detail="Failed to update phone number")


@router.delete("/{phone_number}")
async def release_phone_number(
    phone_number: str = Path(..., description="Phone number to release"),
    force: bool = Query(False, description="Force release even if active"),
    current_user: User = Depends(get_current_active_user),
    phone_service: PhoneNumberService = Depends(get_phone_number_service),
):
    """
    Release (delete) a phone number

    Args:
        phone_number: Phone number to release
        force: Force release even if active
        current_user: Authenticated user
        phone_service: Phone number service

    Returns:
        Dict: Release confirmation
    """
    try:
        # Release the number
        result = await phone_service.cancel_phone_number(
            user_id=current_user.id, phone_number_id=phone_number
        )

        return {
            "message": "Phone number released successfully",
            "phone_number": phone_number,
            "released_at": datetime.utcnow(),
        }

    except ValueError as e:
        logger.warning(f"Cannot release number: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to release number: {e}")
        raise HTTPException(status_code=500, detail="Failed to release phone number")


@router.get("/{phone_number}/usage", response_model=NumberUsageResponse)
async def get_number_usage(
    phone_number: str = Path(..., description="Phone number"),
    period_days: int = Query(30, ge=1, le=365, description="Usage period in days"),
    current_user: User = Depends(get_current_active_user),
    phone_service: PhoneNumberService = Depends(get_phone_number_service),
):
    """
    Get usage statistics for a phone number

    Args:
        phone_number: Phone number ID
        period_days: Usage period in days
        current_user: Authenticated user
        phone_service: Phone number service

    Returns:
        NumberUsageResponse: Usage statistics
    """
    try:
        # Get usage statistics
        usage_stats = await phone_service.get_usage_statistics(
            user_id=current_user.id,
            phone_number_id=phone_number,
        )

        return NumberUsageResponse(
            phone_number=phone_number,
            period_start=usage_stats["period_start"],
            period_end=usage_stats["period_end"],
            messages_sent=usage_stats["messages_sent"],
            messages_received=usage_stats["messages_received"],
            calls_made=usage_stats["calls_made"],
            calls_received=usage_stats["calls_received"],
            total_cost=float(usage_stats["costs"]["total_cost"]),
            cost_breakdown=usage_stats["cost_breakdown"],
            usage_by_country={},  # Placeholder
        )

    except ValueError as e:
        logger.warning(f"Number not found: {e}")
        raise HTTPException(status_code=404, detail="Phone number not found")
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve usage statistics"
        )


@router.post("/cost-estimate", response_model=CostEstimateResponse)
async def calculate_cost_estimate(
    request: CostCalculationRequest,
    routing_engine: SmartRoutingEngine = Depends(get_routing_engine),
):
    """
    Calculate cost estimates for communication between countries

    Args:
        request: Cost calculation request
        routing_engine: Smart routing engine

    Returns:
        CostEstimateResponse: Cost estimates and recommendations
    """
    try:
        # Calculate costs
        cost_estimate = await routing_engine.calculate_communication_costs(
            from_country=request.from_country,
            to_country=request.to_country,
            message_count=request.message_count,
            call_minutes=request.call_minutes,
            number_type=request.number_type,
        )

        return CostEstimateResponse(
            from_country=request.from_country,
            to_country=request.to_country,
            message_cost=cost_estimate["message_cost"],
            call_cost_per_minute=cost_estimate["call_cost_per_minute"],
            total_estimated_cost=cost_estimate["total_estimated_cost"],
            currency=cost_estimate["currency"],
            cost_breakdown=cost_estimate["cost_breakdown"],
            recommendations=cost_estimate["recommendations"],
        )

    except Exception as e:
        logger.error(f"Failed to calculate costs: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate cost estimate")


@router.post("/optimize", response_model=OptimizationRecommendationResponse)
async def get_optimization_recommendations(
    request: NumberOptimizationRequest,
    current_user: User = Depends(get_current_active_user),
    routing_engine: SmartRoutingEngine = Depends(
        get_routing_engine
    ),  # This can be enhanced
):
    """
    Get optimization recommendations for number portfolio

    Args:
        request: Optimization request
        current_user: Authenticated user
        routing_engine: Smart routing engine

    Returns:
        OptimizationRecommendationResponse: Optimization recommendations
    """
    try:
        # Get optimization recommendations
        recommendations = await routing_engine.optimize_number_portfolio(
            user_id=current_user.id,
            target_countries=request.target_countries,
            monthly_message_volume=request.monthly_message_volume,
            monthly_call_minutes=request.monthly_call_minutes,
            budget_limit=request.budget_limit,
            optimization_goal=request.optimization_goal,
        )

        return OptimizationRecommendationResponse(
            current_setup=recommendations["current_setup"],
            recommended_setup=recommendations["recommended_setup"],
            potential_savings=recommendations["potential_savings"],
            coverage_improvement=recommendations["coverage_improvement"],
            delivery_improvement=recommendations["delivery_improvement"],
            implementation_steps=recommendations["implementation_steps"],
            cost_comparison=recommendations["cost_comparison"],
        )

    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate optimization recommendations"
        )


@router.get("/analytics", response_model=NumberAnalyticsResponse)
async def get_number_analytics(
    period_days: int = Query(30, ge=1, le=365, description="Analytics period in days"),
    current_user: User = Depends(get_current_active_user),
    phone_service: PhoneNumberService = Depends(get_phone_number_service),
):
    """
    Get comprehensive analytics for user's number portfolio

    Args:
        period_days: Analytics period in days
        current_user: Authenticated user
        phone_service: Phone number service

    Returns:
        NumberAnalyticsResponse: Comprehensive analytics
    """
    try:
        # Get analytics data
        analytics = await phone_service.get_portfolio_analytics(
            user_id=current_user.id, period_days=period_days
        )

        return NumberAnalyticsResponse(
            total_numbers=analytics["total_numbers"],
            active_numbers=analytics["active_numbers"],
            total_monthly_cost=float(analytics["total_monthly_cost"]),
            usage_efficiency=float(analytics["usage_efficiency"]),
            top_performing_numbers=analytics["top_performing_numbers"],
            underutilized_numbers=analytics["underutilized_numbers"],
            cost_trends=analytics["cost_trends"],
            recommendations=analytics["recommendations"],
        )

    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve number analytics"
        )


@router.get("/countries/supported")
async def get_supported_countries(
    phone_service: PhoneNumberService = Depends(get_phone_number_service),
):
    """
    Get list of supported countries for number purchase

    Args:
        phone_service: Phone number service

    Returns:
        Dict: Supported countries with capabilities and pricing
    """
    try:
        supported_countries = await phone_service.get_supported_countries()

        return {
            "countries": supported_countries,
            "total_count": len(supported_countries),
            "last_updated": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Failed to get supported countries: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve supported countries"
        )


@router.get("/health")
async def health_check(
    twilio_client: EnhancedTwilioClient = Depends(get_twilio_client),
):
    """
    Check the health status of the number management service

    Args:
        twilio_client: Enhanced Twilio client

    Returns:
        Dict: Service health status
    """
    try:
        # Check Twilio API connectivity
        health_status = await twilio_client.check_api_health()

        return {
            "status": "healthy" if health_status["api_accessible"] else "degraded",
            "timestamp": datetime.utcnow(),
            "twilio_status": health_status["status"],
            "available_countries": health_status.get("available_countries", 0),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "timestamp": datetime.utcnow(), "error": str(e)}


# Background Tasks


async def setup_purchased_number(
    phone_number: str, user_id: str, webhook_url: Optional[str]
):
    """
    Background task to set up a newly purchased number

    Args:
        phone_number: Purchased phone number
        user_id: User identifier
        webhook_url: Webhook URL for the number
    """
    try:
        logger.info(f"Setting up purchased number {phone_number} for user {user_id}")

        # In production, this would:
        # 1. Configure webhooks
        # 2. Set up routing rules
        # 3. Initialize usage tracking
        # 4. Send confirmation notifications
        # 5. Update billing systems

        await asyncio.sleep(1)  # Placeholder for actual setup logic

        logger.info(f"Number setup completed for {phone_number}")

    except Exception as e:
        logger.error(f"Number setup failed for {phone_number}: {e}")


# Export router
__all__ = ["router"]
