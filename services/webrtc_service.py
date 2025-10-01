import json
import asyncio
from typing import List, Optional, Dict, Any
from models.call_models import Call, WebRTCSession
from core.database import SessionLocal
from datetime import datetime
from core.error_handler import handle_errors

class WebRTCService:
    def __init__(self):
        self.db = SessionLocal()
        self.active_sessions: Dict[int, Dict[str, Any]] = {}  # session_id -> session data
        self.connection_quality_threshold = 0.7  # Minimum quality score

    def initiate_call(self, caller_id: int, receiver_id: int, call_type: str):
        call = Call(caller_id=caller_id, receiver_id=receiver_id, call_type=call_type, status='initiated')
        self.db.add(call)
        self.db.commit()
        self.db.refresh(call)
        return call

    def create_webrtc_session(self, call_id: int):
        session = WebRTCSession(call_id=call_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def update_offer(self, session_id: int, offer: str):
        session = self.db.query(WebRTCSession).filter(WebRTCSession.id == session_id).first()
        if session:
            session.offer = offer
            self.db.commit()
        return session

    def update_answer(self, session_id: int, answer: str):
        session = self.db.query(WebRTCSession).filter(WebRTCSession.id == session_id).first()
        if session:
            session.answer = answer
            self.db.commit()
        return session

    def add_ice_candidate(self, session_id: int, candidate: str):
        session = self.db.query(WebRTCSession).filter(WebRTCSession.id == session_id).first()
        if session:
            if session.ice_candidates:
                session.ice_candidates += f',{candidate}'
            else:
                session.ice_candidates = candidate
            self.db.commit()
        return session

    def end_call(self, call_id: int):
        call = self.db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.status = 'ended'
            call.end_time = datetime.utcnow()
            if call.start_time and call.end_time:
                call.duration = int((call.end_time - call.start_time).total_seconds())
            self.db.commit()
        return call

    def get_call(self, call_id: int):
        return self.db.query(Call).filter(Call.id == call_id).first()

    def get_webrtc_session(self, session_id: int):
        return self.db.query(WebRTCSession).filter(WebRTCSession.id == session_id).first()

    @handle_errors
    def create_conference_call(self, caller_id: int, participant_ids: List[int], call_type: str = 'video'):
        """Create a multi-party conference call"""
        call = Call(
            caller_id=caller_id,
            receiver_id=participant_ids[0] if participant_ids else caller_id,  # Primary receiver
            call_type=call_type,
            status='conference_initiated'
        )
        self.db.add(call)
        self.db.commit()
        self.db.refresh(call)

        # Create WebRTC sessions for all participants
        sessions = []
        for participant_id in [caller_id] + participant_ids:
            session = WebRTCSession(call_id=call.id)
            self.db.add(session)
            sessions.append(session)

        self.db.commit()

        # Initialize active session tracking
        self.active_sessions[call.id] = {
            'participants': [caller_id] + participant_ids,
            'start_time': datetime.utcnow(),
            'quality_scores': {pid: 1.0 for pid in [caller_id] + participant_ids}
        }

        return call, sessions

    @handle_errors
    def join_conference(self, call_id: int, participant_id: int):
        """Add a participant to an existing conference call"""
        call = self.get_call(call_id)
        if not call or call.status not in ['conference_initiated', 'ongoing']:
            raise ValueError("Invalid call or call not in conference mode")

        # Create WebRTC session for new participant
        session = WebRTCSession(call_id=call_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # Update active session tracking
        if call_id in self.active_sessions:
            self.active_sessions[call_id]['participants'].append(participant_id)
            self.active_sessions[call_id]['quality_scores'][participant_id] = 1.0

        return session

    @handle_errors
    def update_connection_quality(self, session_id: int, participant_id: int, quality_score: float):
        """Update connection quality for a participant"""
        session = self.get_webrtc_session(session_id)
        if not session:
            return False

        call_id = session.call_id
        if call_id in self.active_sessions:
            self.active_sessions[call_id]['quality_scores'][participant_id] = quality_score

            # Check if call quality is below threshold
            avg_quality = sum(self.active_sessions[call_id]['quality_scores'].values()) / len(self.active_sessions[call_id]['quality_scores'])
            if avg_quality < self.connection_quality_threshold:
                self._handle_poor_connection(call_id)

        return True

    def _handle_poor_connection(self, call_id: int):
        """Handle poor connection quality by suggesting optimizations"""
        # This could trigger notifications, quality adjustments, etc.
        print(f"Poor connection quality detected for call {call_id}")
        # TODO: Implement quality improvement suggestions

    @handle_errors
    def get_call_participants(self, call_id: int) -> List[int]:
        """Get all participants in a call"""
        if call_id in self.active_sessions:
            return self.active_sessions[call_id]['participants']
        return []

    @handle_errors
    def get_call_quality_stats(self, call_id: int) -> Dict[str, Any]:
        """Get quality statistics for a call"""
        if call_id not in self.active_sessions:
            return {}

        session_data = self.active_sessions[call_id]
        quality_scores = session_data['quality_scores']

        return {
            'participant_count': len(session_data['participants']),
            'average_quality': sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0,
            'min_quality': min(quality_scores.values()) if quality_scores else 0,
            'max_quality': max(quality_scores.values()) if quality_scores else 0,
            'duration': (datetime.utcnow() - session_data['start_time']).total_seconds(),
            'quality_below_threshold': any(score < self.connection_quality_threshold for score in quality_scores.values())
        }

    @handle_errors
    def start_call_recording(self, call_id: int, recording_type: str = 'audio_video'):
        """Start recording a call"""
        call = self.get_call(call_id)
        if not call:
            raise ValueError("Call not found")

        # Update call status to indicate recording
        call.status = 'recording'
        self.db.commit()

        # TODO: Implement actual recording logic with media server
        return {
            'call_id': call_id,
            'recording_type': recording_type,
            'started_at': datetime.utcnow().isoformat(),
            'status': 'started'
        }

    @handle_errors
    def stop_call_recording(self, call_id: int):
        """Stop recording a call"""
        call = self.get_call(call_id)
        if not call or call.status != 'recording':
            raise ValueError("Call not found or not recording")

        call.status = 'ongoing'  # Or keep as 'ended' if call is ending
        self.db.commit()

        # TODO: Implement recording file processing and storage
        return {
            'call_id': call_id,
            'stopped_at': datetime.utcnow().isoformat(),
            'status': 'stopped'
        }

    @handle_errors
    def get_call_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get call history for a user"""
        calls = self.db.query(Call).filter(
            ((Call.caller_id == user_id) | (Call.receiver_id == user_id))
        ).order_by(Call.start_time.desc()).limit(limit).all()

        history = []
        for call in calls:
            history.append({
                'id': call.id,
                'type': call.call_type,
                'status': call.status,
                'start_time': call.start_time.isoformat() if call.start_time else None,
                'end_time': call.end_time.isoformat() if call.end_time else None,
                'duration': call.duration,
                'is_caller': call.caller_id == user_id,
                'other_party': call.receiver.username if call.caller_id == user_id else call.caller.username
            })

        return history

    @handle_errors
    def cleanup_inactive_sessions(self):
        """Clean up inactive WebRTC sessions and calls"""
        # Find calls that have been in 'initiated' status for too long
        cutoff_time = datetime.utcnow()  # Could be configurable
        old_calls = self.db.query(Call).filter(
            Call.status == 'initiated',
            Call.start_time < cutoff_time
        ).all()

        for call in old_calls:
            call.status = 'expired'
            # Clean up associated sessions
            sessions = self.db.query(WebRTCSession).filter(WebRTCSession.call_id == call.id).all()
            for session in sessions:
                self.db.delete(session)

        self.db.commit()

        # Clean up active sessions tracking
        current_time = datetime.utcnow()
        to_remove = []
        for call_id, session_data in self.active_sessions.items():
            # Remove sessions older than 24 hours
            if (current_time - session_data['start_time']).total_seconds() > 86400:
                to_remove.append(call_id)

        for call_id in to_remove:
            del self.active_sessions[call_id]

        return len(old_calls), len(to_remove)
