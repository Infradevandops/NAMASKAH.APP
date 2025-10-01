#!/usr/bin/env python3
"""
WebSocket API endpoints for real-time communication
"""
import logging
from typing import Optional

from fastapi import (APIRouter, Depends, HTTPException, Query, WebSocket,
                     WebSocketDisconnect, status)
from fastapi.responses import HTMLResponse

from models import User
from services.auth_service import get_current_active_user
from services.websocket_manager import connection_manager, websocket_handler
from services.webrtc_service import WebRTCService
from core.database import get_db
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Global WebRTC signaling rooms
webrtc_rooms: Dict[str, Dict[str, WebSocket]] = {}  # room_id -> {user_id: websocket}


@router.websocket("/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
):
    """
    WebSocket endpoint for real-time chat communication

    Authentication:
    - Pass JWT token as query parameter: /ws/chat?token=your_jwt_token
    - Or send token in first message: {"type": "auth", "token": "your_jwt_token"}
    """
    if not token:
        # Try to get token from first message
        await websocket.accept()
        try:
            import json

            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "auth":
                token = message.get("token")
            else:
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Authentication required",
                )
                return
        except Exception:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid authentication message",
            )
            return

    if not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Token required"
        )
        return

    # Handle WebSocket connection with authentication
    await websocket_handler.handle_websocket(websocket, token)


@router.websocket("/webrtc/{call_id}")
async def webrtc_signaling_endpoint(
    websocket: WebSocket,
    call_id: str,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
):
    """
    WebRTC signaling endpoint for voice/video calls

    Supports:
    - offer/answer exchange
    - ICE candidate exchange
    - Call participant management
    - Connection quality monitoring

    Authentication:
    - Pass JWT token as query parameter: /ws/webrtc/{call_id}?token=your_jwt_token
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
            logger.error(f"WebRTC authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        return

    # Initialize WebRTC service
    db = next(get_db())
    webrtc_service = WebRTCService()

    # Join WebRTC room
    room_id = call_id
    if room_id not in webrtc_rooms:
        webrtc_rooms[room_id] = {}

    webrtc_rooms[room_id][str(user_id)] = websocket

    logger.info(f"User {user_id} joined WebRTC room {room_id}")

    try:
        while True:
            # Receive WebRTC signaling message
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")
            target_user_id = message.get("target_user_id")

            # Add sender information
            message["from_user_id"] = str(user_id)
            message["timestamp"] = "now"

            if message_type == "join_call":
                # User joining the call
                participants = webrtc_service.get_call_participants(int(call_id))
                await websocket.send_text(json.dumps({
                    "type": "call_participants",
                    "participants": participants,
                    "call_id": call_id
                }))

            elif message_type in ["offer", "answer", "ice_candidate"]:
                # Forward signaling messages to target user
                if target_user_id and target_user_id in webrtc_rooms.get(room_id, {}):
                    target_ws = webrtc_rooms[room_id][target_user_id]
                    await target_ws.send_text(json.dumps(message))
                else:
                    # Broadcast to all participants in the room (for conference calls)
                    for participant_id, participant_ws in webrtc_rooms.get(room_id, {}).items():
                        if participant_id != str(user_id):
                            try:
                                await participant_ws.send_text(json.dumps(message))
                            except Exception as e:
                                logger.error(f"Failed to send message to participant {participant_id}: {e}")

            elif message_type == "quality_update":
                # Update connection quality
                quality_score = message.get("quality_score", 1.0)
                webrtc_service.update_connection_quality(
                    int(message.get("session_id", 0)),
                    int(user_id),
                    quality_score
                )

            elif message_type == "leave_call":
                # User leaving the call
                break

            elif message_type == "ping":
                # Respond to ping for connection health
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": "now"
                }))

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from WebRTC room {room_id}")
    except Exception as e:
        logger.error(f"WebRTC signaling error for user {user_id}: {e}")
    finally:
        # Clean up: remove user from room
        if room_id in webrtc_rooms and str(user_id) in webrtc_rooms[room_id]:
            del webrtc_rooms[room_id][str(user_id)]

            # If room is empty, clean it up
            if not webrtc_rooms[room_id]:
                del webrtc_rooms[room_id]

        logger.info(f"Cleaned up WebRTC connection for user {user_id} in room {room_id}")


@router.get("/status")
async def websocket_status(current_user: User = Depends(get_current_active_user)):
    """
    Get WebSocket connection status and online users
    """
    try:
        online_users = connection_manager.get_online_users()
        is_online = connection_manager.is_user_online(current_user.id)

        return {
            "user_id": current_user.id,
            "is_connected": is_online,
            "online_users_count": len(online_users),
            "online_users": online_users[:10],  # Limit for privacy
            "websocket_url": "/ws/chat",
        }

    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get WebSocket status",
        )


@router.post("/broadcast/{conversation_id}")
async def broadcast_to_conversation(
    conversation_id: str,
    message: dict,
    current_user: User = Depends(get_current_active_user),
):
    """
    Broadcast a message to all users in a conversation (admin/testing endpoint)
    """
    try:
        # Verify user has access to conversation
        from core.database import get_db
        from services.conversation_service import ConversationService

        db = next(get_db())
        conversation_service = ConversationService(db)

        conversation = await conversation_service.get_conversation(
            conversation_id, current_user.id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        # Broadcast message
        sent_count = await connection_manager.send_to_conversation(
            conversation_id,
            {
                "type": "broadcast",
                "message": message,
                "from_user": current_user.id,
                "timestamp": "now",
            },
        )

        return {
            "success": True,
            "sent_to": sent_count,
            "conversation_id": conversation_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting to conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast message",
        )


@router.get("/health")
async def websocket_health():
    """
    WebSocket service health check
    """
    online_count = len(connection_manager.get_online_users())

    active_webrtc_rooms = len(webrtc_rooms)

    return {
        "status": "healthy",
        "service": "websocket",
        "version": "2.0.0",
        "online_users": online_count,
        "active_webrtc_rooms": active_webrtc_rooms,
        "features": [
            "jwt_authentication",
            "real_time_messaging",
            "typing_indicators",
            "presence_tracking",
            "message_delivery",
            "conversation_broadcasting",
            "webrtc_signaling",
            "voice_video_calls",
            "conference_calls",
            "connection_quality_monitoring",
        ],
    }


# WebSocket connection test page
@router.get("/test", response_class=HTMLResponse)
async def websocket_test_page():
    """
    Simple WebSocket test page for development
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
            input, button { margin: 5px; padding: 5px; }
            .message { margin: 5px 0; padding: 5px; background: #f0f0f0; }
            .error { color: red; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        
        <div>
            <input type="text" id="token" placeholder="JWT Token" style="width: 400px;">
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        
        <div>
            <input type="text" id="conversationId" placeholder="Conversation ID">
            <button onclick="joinConversation()">Join Conversation</button>
        </div>
        
        <div>
            <input type="text" id="messageInput" placeholder="Type a message..." style="width: 300px;">
            <button onclick="sendMessage()">Send Message</button>
        </div>
        
        <div>
            <button onclick="startTyping()">Start Typing</button>
            <button onclick="stopTyping()">Stop Typing</button>
            <button onclick="getOnlineUsers()">Get Online Users</button>
        </div>
        
        <div id="messages"></div>
        
        <script>
            let ws = null;
            let currentConversationId = null;
            
            function addMessage(message, className = '') {
                const messages = document.getElementById('messages');
                const div = document.createElement('div');
                div.className = 'message ' + className;
                div.innerHTML = '<strong>' + new Date().toLocaleTimeString() + ':</strong> ' + message;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }
            
            function connect() {
                const token = document.getElementById('token').value;
                if (!token) {
                    addMessage('Please enter a JWT token', 'error');
                    return;
                }
                
                if (ws) {
                    ws.close();
                }
                
                ws = new WebSocket(`ws://localhost:8000/ws/chat?token=${token}`);
                
                ws.onopen = function(event) {
                    addMessage('Connected to WebSocket', 'success');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage('Received: ' + JSON.stringify(data, null, 2));
                };
                
                ws.onclose = function(event) {
                    addMessage('WebSocket connection closed', 'error');
                };
                
                ws.onerror = function(error) {
                    addMessage('WebSocket error: ' + error, 'error');
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function joinConversation() {
                const conversationId = document.getElementById('conversationId').value;
                if (!conversationId || !ws) return;
                
                currentConversationId = conversationId;
                ws.send(JSON.stringify({
                    type: 'join_conversation',
                    conversation_id: conversationId
                }));
            }
            
            function sendMessage() {
                const message = document.getElementById('messageInput').value;
                if (!message || !ws || !currentConversationId) return;
                
                ws.send(JSON.stringify({
                    type: 'send_message',
                    conversation_id: currentConversationId,
                    content: message,
                    message_type: 'CHAT'
                }));
                
                document.getElementById('messageInput').value = '';
            }
            
            function startTyping() {
                if (!ws || !currentConversationId) return;
                
                ws.send(JSON.stringify({
                    type: 'typing',
                    conversation_id: currentConversationId,
                    is_typing: true
                }));
            }
            
            function stopTyping() {
                if (!ws || !currentConversationId) return;
                
                ws.send(JSON.stringify({
                    type: 'typing',
                    conversation_id: currentConversationId,
                    is_typing: false
                }));
            }
            
            function getOnlineUsers() {
                if (!ws) return;
                
                ws.send(JSON.stringify({
                    type: 'get_online_users'
                }));
            }
            
            // Auto-connect on Enter key
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
