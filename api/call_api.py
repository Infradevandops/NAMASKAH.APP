from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from services.webrtc_service import WebRTCService
from models import User
from services.auth_service import get_current_active_user

router = APIRouter(prefix="/calls", tags=["calls"])
webrtc_service = WebRTCService()

class InitiateCallRequest(BaseModel):
    receiver_id: int
    call_type: str  # 'voice' or 'video'

class WebRTCUpdateRequest(BaseModel):
    offer: str = None
    answer: str = None
    ice_candidate: str = None

class ConferenceCallRequest(BaseModel):
    participant_ids: List[int] = Field(..., description="List of participant user IDs")
    call_type: str = Field(default="video", description="'voice' or 'video'")

class JoinConferenceRequest(BaseModel):
    participant_id: int = Field(..., description="User ID of participant joining")

class QualityUpdateRequest(BaseModel):
    session_id: int = Field(..., description="WebRTC session ID")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Connection quality score (0.0-1.0)")

class RecordingRequest(BaseModel):
    recording_type: str = Field(default="audio_video", description="'audio', 'video', or 'audio_video'")

class CallHistoryRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of calls to return")

@router.post("/")
def initiate_call(request: InitiateCallRequest, user_id: int = None):  # user_id from auth
    call = webrtc_service.initiate_call(user_id, request.receiver_id, request.call_type)
    session = webrtc_service.create_webrtc_session(call.id)
    return {"call": call, "session": session}

@router.put("/{session_id}/offer")
def update_offer(session_id: int, request: WebRTCUpdateRequest):
    session = webrtc_service.update_offer(session_id, request.offer)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.put("/{session_id}/answer")
def update_answer(session_id: int, request: WebRTCUpdateRequest):
    session = webrtc_service.update_answer(session_id, request.answer)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/{session_id}/ice")
def add_ice_candidate(session_id: int, request: WebRTCUpdateRequest):
    session = webrtc_service.add_ice_candidate(session_id, request.ice_candidate)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.put("/{call_id}/end")
def end_call(call_id: int):
    call = webrtc_service.end_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call

@router.get("/{call_id}")
def get_call(call_id: int):
    call = webrtc_service.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call

@router.get("/sessions/{session_id}")
def get_webrtc_session(session_id: int):
    session = webrtc_service.get_webrtc_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/conference")
def create_conference_call(
    request: ConferenceCallRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Create a multi-party conference call"""
    try:
        call, sessions = webrtc_service.create_conference_call(
            current_user.id,
            request.participant_ids,
            request.call_type
        )
        return {
            "call": call,
            "sessions": sessions,
            "participants": [current_user.id] + request.participant_ids
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create conference call: {str(e)}")

@router.post("/{call_id}/join")
def join_conference_call(
    call_id: int,
    request: JoinConferenceRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Add a participant to an existing conference call"""
    try:
        session = webrtc_service.join_conference(call_id, request.participant_id)
        return {
            "call_id": call_id,
            "session": session,
            "participant_id": request.participant_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to join conference call: {str(e)}")

@router.post("/{call_id}/quality")
def update_call_quality(
    call_id: int,
    request: QualityUpdateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Update connection quality for a call participant"""
    try:
        success = webrtc_service.update_connection_quality(
            request.session_id,
            current_user.id,
            request.quality_score
        )
        return {
            "success": success,
            "call_id": call_id,
            "participant_id": current_user.id,
            "quality_score": request.quality_score
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update quality: {str(e)}")

@router.get("/{call_id}/quality")
def get_call_quality_stats(
    call_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get quality statistics for a call"""
    try:
        stats = webrtc_service.get_call_quality_stats(call_id)
        return {
            "call_id": call_id,
            "quality_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get quality stats: {str(e)}")

@router.post("/{call_id}/recording/start")
def start_call_recording(
    call_id: int,
    request: RecordingRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Start recording a call"""
    try:
        result = webrtc_service.start_call_recording(call_id, request.recording_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to start recording: {str(e)}")

@router.post("/{call_id}/recording/stop")
def stop_call_recording(
    call_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Stop recording a call"""
    try:
        result = webrtc_service.stop_call_recording(call_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to stop recording: {str(e)}")

@router.get("/history")
def get_call_history(
    request: CallHistoryRequest = CallHistoryRequest(),
    current_user: User = Depends(get_current_active_user)
):
    """Get call history for the current user"""
    try:
        history = webrtc_service.get_call_history(current_user.id, request.limit)
        return {
            "user_id": current_user.id,
            "call_history": history,
            "total_count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get call history: {str(e)}")

@router.get("/{call_id}/participants")
def get_call_participants(
    call_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get all participants in a call"""
    try:
        participants = webrtc_service.get_call_participants(call_id)
        return {
            "call_id": call_id,
            "participants": participants,
            "participant_count": len(participants)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get participants: {str(e)}")

@router.post("/cleanup")
def cleanup_inactive_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """Clean up inactive WebRTC sessions and calls (admin function)"""
    try:
        expired_calls, old_sessions = webrtc_service.cleanup_inactive_sessions()
        return {
            "expired_calls_cleaned": expired_calls,
            "old_sessions_cleaned": old_sessions,
            "message": f"Cleaned up {expired_calls} expired calls and {old_sessions} old sessions"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to cleanup sessions: {str(e)}")

@router.get("/health")
def call_service_health():
    """Call service health check"""
    return {
        "status": "healthy",
        "service": "calls",
        "version": "2.0.0",
        "features": [
            "voice_video_calls",
            "conference_calls",
            "call_recording",
            "quality_monitoring",
            "call_history",
            "webrtc_signaling"
        ]
    }
