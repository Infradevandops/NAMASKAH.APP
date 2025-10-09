#!/usr/bin/env python3
"""
Admin API endpoints for platform management
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
async def get_platform_stats():
    """Get platform statistics"""
    return {
        "users": {"total": 1247, "active": 892, "new_today": 23},
        "verifications": {"total": 8932, "today": 47, "success_rate": 98.5},
        "revenue": {"total": 4567.89, "monthly": 1234.56, "average_order": 12.45},
        "system": {
            "uptime": "99.9%",
            "api_status": "operational",
            "database_status": "connected",
        },
    }


@router.get("/users")
async def get_users(limit: int = 50, offset: int = 0):
    """Get user list for admin management"""
    # Mock user data
    users = [
        {
            "id": 1,
            "email": "demo@namaskah.com",
            "username": "demo",
            "credits": 25.50,
            "status": "active",
            "created_at": "2024-01-15T10:30:00Z",
            "last_login": "2024-01-20T14:22:00Z",
            "total_verifications": 15,
        }
    ]

    return {"users": users, "total": len(users), "limit": limit, "offset": offset}


@router.get("/verifications")
async def get_verifications(status: str = None, limit: int = 50):
    """Get verification list for monitoring"""
    # Mock verification data
    verifications = [
        {
            "id": "v_001",
            "user_id": 1,
            "service": "whatsapp",
            "number": "+1234567890",
            "status": "completed",
            "created_at": "2024-01-20T10:30:00Z",
            "completed_at": "2024-01-20T10:32:15Z",
            "cost": 0.50,
        }
    ]

    if status:
        verifications = [v for v in verifications if v["status"] == status]

    return {
        "verifications": verifications,
        "total": len(verifications),
        "active": 23,
        "completed": 156,
        "failed": 3,
    }


@router.get("/revenue")
async def get_revenue_analytics():
    """Get revenue analytics"""
    return {
        "daily": [
            {"date": "2024-01-20", "amount": 156.78},
            {"date": "2024-01-19", "amount": 234.56},
            {"date": "2024-01-18", "amount": 189.34},
        ],
        "monthly": {"current": 4567.89, "previous": 3712.45, "growth": 23.0},
        "top_services": [
            {"service": "whatsapp", "revenue": 1234.56, "count": 2468},
            {"service": "google", "revenue": 987.65, "count": 3291},
            {"service": "telegram", "revenue": 654.32, "count": 2617},
        ],
    }


@router.get("/system/health")
async def get_system_health():
    """Get system health status"""
    return {
        "status": "healthy",
        "services": {
            "api": {"status": "operational", "response_time": "45ms"},
            "database": {"status": "connected", "connections": 12},
            "sms_service": {"status": "mock_mode", "provider": "twilio"},
            "payment_service": {"status": "mock_mode", "provider": "stripe"},
            "verification_service": {"status": "mock_mode", "provider": "textverified"},
        },
        "metrics": {
            "uptime": "99.9%",
            "requests_per_minute": 45,
            "error_rate": "0.1%",
            "avg_response_time": "120ms",
        },
    }


@router.post("/users/{user_id}/suspend")
async def suspend_user(user_id: int):
    """Suspend a user account"""
    return {"message": f"User {user_id} suspended successfully"}


@router.post("/users/{user_id}/activate")
async def activate_user(user_id: int):
    """Activate a user account"""
    return {"message": f"User {user_id} activated successfully"}


@router.post("/system/maintenance")
async def toggle_maintenance_mode(enabled: bool = True):
    """Toggle maintenance mode"""
    status = "enabled" if enabled else "disabled"
    return {"message": f"Maintenance mode {status}"}


@router.get("/logs")
async def get_system_logs(level: str = "info", limit: int = 100):
    """Get system logs"""
    # Mock log data
    logs = [
        {
            "timestamp": "2024-01-20T10:30:00Z",
            "level": "info",
            "message": "User login successful",
            "user_id": 1,
        },
        {
            "timestamp": "2024-01-20T10:29:45Z",
            "level": "info",
            "message": "SMS verification completed",
            "verification_id": "v_001",
        },
    ]

    return {"logs": logs, "total": len(logs)}
