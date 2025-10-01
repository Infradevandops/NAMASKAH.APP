#!/usr/bin/env python3
"""
Verification WebSocket API endpoints for real-time status updates
"""
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, Query, status
from typing import Dict
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["verification_websocket"])

# Global verification WebSocket rooms
verification_rooms: Dict[str, Dict[str, WebSocket]] = {}  # verification_id -> {user_id: websocket}


@router.websocket("/verification/{verification_id}")
async def verification_websocket_endpoint(
    websocket: WebSocket,
    verification_id: str,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
):
    """
    WebSocket endpoint for real-time verification status updates

    Provides live updates for verification processes including:
    - Status changes (pending -> processing -> completed/failed)
    - Progress updates
    - Error notifications
    - Auto-completion notifications

    Authentication:
    - Pass JWT token as query parameter: /ws/verification/{verification_id}?token=your_jwt_token
    """
    await websocket.accept()

    # Authenticate user
    user_id = None
    if token:
        try:
            from auth.jwt_handler import decode_token
            payload = decode_token(token)
            user_id = payload.get("sub")
        except Exception as e:
            logger.error(f"Verification WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        return

    # Verify user owns this verification
    from core.database import get_db
    from services.verification_service import VerificationService
    from clients.unified_client import get_unified_client

    db = next(get_db())
    verification_service = VerificationService(db, get_unified_client().textverified_client)

    try:
        verification = await verification_service._get_user_verification(
            user_id=int(user_id), verification_id=verification_id
        )
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Verification not found or access denied")
        return

    # Join verification room
    room_id = verification_id
    if room_id not in verification_rooms:
        verification_rooms[room_id] = {}

    verification_rooms[room_id][str(user_id)] = websocket

    logger.info(f"User {user_id} joined verification room {room_id}")

    try:
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "verification_status",
            "verification_id": verification_id,
            "status": verification.status,
            "timestamp": "now"
        }))

        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "ping":
                # Respond to ping for connection health
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": "now"
                }))

            elif message_type == "get_status":
                # Send current verification status
                # Refresh verification from database
                db.refresh(verification)
                await websocket.send_text(json.dumps({
                    "type": "verification_status",
                    "verification_id": verification_id,
                    "status": verification.status,
                    "phone_number": verification.phone_number,
                    "verification_code": verification.verification_code,
                    "timestamp": "now"
                }))

    except Exception as e:
        logger.error(f"Verification WebSocket error for user {user_id}: {e}")
    finally:
        # Clean up: remove user from room
        if room_id in verification_rooms and str(user_id) in verification_rooms[room_id]:
            del verification_rooms[room_id][str(user_id)]

            # If room is empty, clean it up
            if not verification_rooms[room_id]:
                del verification_rooms[room_id]

        logger.info(f"Cleaned up verification WebSocket connection for user {user_id} in room {room_id}")


def send_verification_status_update(verification_id: str, status_data: dict):
    """
    Send status update to all users in a verification room
    """
    room_id = verification_id
    if room_id in verification_rooms:
        message = {
            "type": "verification_status",
            "verification_id": verification_id,
            **status_data,
            "timestamp": "now"
        }

        for user_id, websocket in verification_rooms[room_id].items():
            try:
                websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send status update to user {user_id}: {e}")
                # Remove broken connection
                del verification_rooms[room_id][user_id]
