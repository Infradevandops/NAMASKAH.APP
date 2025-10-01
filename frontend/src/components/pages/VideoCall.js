import React, { useRef, useEffect, useState, useCallback } from 'react';
import axios from 'axios';

const VideoCall = ({ callId, onEndCall, isConference = false, participants = [] }) => {
  const localVideoRef = useRef(null);
  const remoteVideoRefs = useRef({});
  const peerConnectionsRef = useRef({});
  const websocketRef = useRef(null);
  const localStreamRef = useRef(null);
  const screenStreamRef = useRef(null);

  const [isConnected, setIsConnected] = useState(false);
  const [callStatus, setCallStatus] = useState('connecting');
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [participants, setParticipants] = useState(participants);
  const [connectionQuality, setConnectionQuality] = useState(1.0);
  const [callDuration, setCallDuration] = useState(0);
  const [callStartTime, setCallStartTime] = useState(null);

  // WebRTC configuration
  const rtcConfiguration = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
      // Add TURN servers here for production
    ]
  };

  useEffect(() => {
    initializeCall();
    return () => {
      cleanup();
    };
  }, [callId]);

  useEffect(() => {
    let interval;
    if (callStartTime) {
      interval = setInterval(() => {
        setCallDuration(Math.floor((Date.now() - callStartTime) / 1000));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [callStartTime]);

  const initializeCall = async () => {
    try {
      setCallStatus('initializing');

      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: true
      });

      localStreamRef.current = stream;
      localVideoRef.current.srcObject = stream;
      setCallStartTime(Date.now());

      // Initialize WebSocket connection for signaling
      await initializeWebSocket();

      setCallStatus('connecting');

    } catch (error) {
      console.error('Error initializing call:', error);
      setCallStatus('error');
    }
  };

  const initializeWebSocket = async () => {
    try {
      const token = localStorage.getItem('token');
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/webrtc/${callId}?token=${token}`;

      websocketRef.current = new WebSocket(wsUrl);

      websocketRef.current.onopen = () => {
        console.log('WebRTC signaling connected');
        // Join the call
        sendSignalingMessage({ type: 'join_call' });
      };

      websocketRef.current.onmessage = handleSignalingMessage;

      websocketRef.current.onclose = () => {
        console.log('WebRTC signaling disconnected');
        setCallStatus('disconnected');
      };

      websocketRef.current.onerror = (error) => {
        console.error('WebRTC signaling error:', error);
        setCallStatus('error');
      };

    } catch (error) {
      console.error('Error initializing WebSocket:', error);
    }
  };

  const handleSignalingMessage = async (event) => {
    try {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'call_participants':
          setParticipants(message.participants);
          // Create peer connections for each participant
          await createPeerConnections(message.participants);
          break;

        case 'offer':
          await handleOffer(message);
          break;

        case 'answer':
          await handleAnswer(message);
          break;

        case 'ice_candidate':
          await handleIceCandidate(message);
          break;

        default:
          console.log('Unknown signaling message:', message.type);
      }
    } catch (error) {
      console.error('Error handling signaling message:', error);
    }
  };

  const createPeerConnections = async (participantIds) => {
    const currentUserId = getCurrentUserId();

    for (const participantId of participantIds) {
      if (participantId === currentUserId) continue;

      const peerConnection = new RTCPeerConnection(rtcConfiguration);
      peerConnectionsRef.current[participantId] = peerConnection;

      // Add local stream tracks
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => {
          peerConnection.addTrack(track, localStreamRef.current);
        });
      }

      // Handle remote stream
      peerConnection.ontrack = (event) => {
        handleRemoteStream(participantId, event.streams[0]);
      };

      // Handle ICE candidates
      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          sendSignalingMessage({
            type: 'ice_candidate',
            target_user_id: participantId.toString(),
            candidate: event.candidate
          });
        }
      };

      // Handle connection state changes
      peerConnection.onconnectionstatechange = () => {
        updateConnectionQuality(participantId, peerConnection);
      };

      // Create offer for this participant
      if (isConference || participantIds.indexOf(participantId) === 0) {
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        sendSignalingMessage({
          type: 'offer',
          target_user_id: participantId.toString(),
          offer: offer
        });
      }
    }
  };

  const handleOffer = async (message) => {
    const { from_user_id, offer } = message;
    const peerConnection = peerConnectionsRef.current[from_user_id];

    if (peerConnection) {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));

      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);

      sendSignalingMessage({
        type: 'answer',
        target_user_id: from_user_id,
        answer: answer
      });
    }
  };

  const handleAnswer = async (message) => {
    const { from_user_id, answer } = message;
    const peerConnection = peerConnectionsRef.current[from_user_id];

    if (peerConnection) {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
      setIsConnected(true);
      setCallStatus('connected');
    }
  };

  const handleIceCandidate = async (message) => {
    const { from_user_id, candidate } = message;
    const peerConnection = peerConnectionsRef.current[from_user_id];

    if (peerConnection) {
      await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
    }
  };

  const handleRemoteStream = (participantId, stream) => {
    if (!remoteVideoRefs.current[participantId]) {
      remoteVideoRefs.current[participantId] = React.createRef();
    }

    if (remoteVideoRefs.current[participantId].current) {
      remoteVideoRefs.current[participantId].current.srcObject = stream;
    }
  };

  const updateConnectionQuality = (participantId, peerConnection) => {
    // Calculate connection quality based on various metrics
    let quality = 1.0;

    if (peerConnection.connectionState === 'connected') {
      // Check stats for quality metrics
      peerConnection.getStats().then(stats => {
        stats.forEach(report => {
          if (report.type === 'inbound-rtp' && report.kind === 'video') {
            const packetsLost = report.packetsLost || 0;
            const packetsReceived = report.packetsReceived || 1;
            const lossRate = packetsLost / (packetsLost + packetsReceived);

            if (lossRate > 0.1) quality = 0.5;
            else if (lossRate > 0.05) quality = 0.7;
          }
        });

        setConnectionQuality(quality);

        // Send quality update to server
        sendSignalingMessage({
          type: 'quality_update',
          session_id: callId,
          quality_score: quality
        });
      });
    }
  };

  const sendSignalingMessage = (message) => {
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message));
    }
  };

  const getCurrentUserId = () => {
    // Get current user ID from context or local storage
    return localStorage.getItem('userId') || 'current_user';
  };

  const toggleMute = () => {
    if (localStreamRef.current) {
      const audioTracks = localStreamRef.current.getAudioTracks();
      audioTracks.forEach(track => {
        track.enabled = isMuted;
      });
      setIsMuted(!isMuted);
    }
  };

  const toggleVideo = () => {
    if (localStreamRef.current) {
      const videoTracks = localStreamRef.current.getVideoTracks();
      videoTracks.forEach(track => {
        track.enabled = isVideoOff;
      });
      setIsVideoOff(!isVideoOff);
    }
  };

  const toggleScreenShare = async () => {
    try {
      if (isScreenSharing) {
        // Stop screen sharing
        if (screenStreamRef.current) {
          screenStreamRef.current.getTracks().forEach(track => track.stop());
          screenStreamRef.current = null;
        }

        // Switch back to camera
        if (localStreamRef.current) {
          localVideoRef.current.srcObject = localStreamRef.current;

          // Update all peer connections
          Object.values(peerConnectionsRef.current).forEach(pc => {
            const sender = pc.getSenders().find(s => s.track?.kind === 'video');
            if (sender && localStreamRef.current) {
              const videoTrack = localStreamRef.current.getVideoTracks()[0];
              sender.replaceTrack(videoTrack);
            }
          });
        }

        setIsScreenSharing(false);
      } else {
        // Start screen sharing
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: { mediaSource: 'screen' },
          audio: true
        });

        screenStreamRef.current = screenStream;
        localVideoRef.current.srcObject = screenStream;

        // Update all peer connections
        Object.values(peerConnectionsRef.current).forEach(pc => {
          const sender = pc.getSenders().find(s => s.track?.kind === 'video');
          if (sender && screenStream) {
            const screenTrack = screenStream.getVideoTracks()[0];
            sender.replaceTrack(screenTrack);
          }
        });

        // Handle screen sharing stop
        screenStream.getVideoTracks()[0].onended = () => {
          toggleScreenShare();
        };

        setIsScreenSharing(true);
      }
    } catch (error) {
      console.error('Error toggling screen share:', error);
    }
  };

  const toggleRecording = async () => {
    try {
      if (isRecording) {
        // Stop recording
        await axios.post(`/api/calls/${callId}/recording/stop`);
        setIsRecording(false);
      } else {
        // Start recording
        await axios.post(`/api/calls/${callId}/recording/start`, {
          recording_type: 'audio_video'
        });
        setIsRecording(true);
      }
    } catch (error) {
      console.error('Error toggling recording:', error);
    }
  };

  const endCall = async () => {
    try {
      // Send leave call message
      sendSignalingMessage({ type: 'leave_call' });

      // End call via API
      await axios.put(`/api/calls/${callId}/end`);

      cleanup();
      onEndCall();
    } catch (error) {
      console.error('Error ending call:', error);
      cleanup();
      onEndCall();
    }
  };

  const cleanup = () => {
    // Close WebSocket
    if (websocketRef.current) {
      websocketRef.current.close();
    }

    // Close all peer connections
    Object.values(peerConnectionsRef.current).forEach(pc => {
      pc.close();
    });
    peerConnectionsRef.current = {};

    // Stop all media tracks
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
    }
    if (screenStreamRef.current) {
      screenStreamRef.current.getTracks().forEach(track => track.stop());
    }

    // Clear refs
    remoteVideoRefs.current = {};
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getGridLayout = () => {
    const totalParticipants = participants.length + 1; // +1 for local user
    if (totalParticipants <= 2) return 'grid-cols-1 md:grid-cols-2';
    if (totalParticipants <= 4) return 'grid-cols-2';
    if (totalParticipants <= 6) return 'grid-cols-2 md:grid-cols-3';
    return 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4';
  };

  return (
    <div className="fixed inset-0 bg-black flex items-center justify-center z-50">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 bg-black bg-opacity-50 text-white p-4 z-10">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold">
              {isConference ? 'Conference Call' : 'Video Call'}
            </h2>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                callStatus === 'connected' ? 'bg-green-500' :
                callStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm capitalize">{callStatus}</span>
            </div>
            {callDuration > 0 && (
              <span className="text-sm font-mono">{formatDuration(callDuration)}</span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {connectionQuality < 1.0 && (
              <div className="flex items-center space-x-1 text-yellow-400">
                <span className="text-sm">Quality: {Math.round(connectionQuality * 100)}%</span>
              </div>
            )}
            <span className="text-sm">{participants.length + 1} participants</span>
          </div>
        </div>
      </div>

      {/* Video Grid */}
      <div className={`w-full h-full p-4 pt-20 pb-24 grid ${getGridLayout()} gap-4`}>
        {/* Local Video */}
        <div className="relative bg-gray-800 rounded-lg overflow-hidden">
          <video
            ref={localVideoRef}
            autoPlay
            muted
            className="w-full h-full object-cover"
          />
          <div className="absolute bottom-2 left-2 bg-black bg-opacity-70 text-white px-3 py-1 rounded-lg flex items-center space-x-2">
            <span>You</span>
            {isMuted && <span className="text-red-400">🔇</span>}
            {isVideoOff && <span className="text-red-400">📷</span>}
            {isScreenSharing && <span className="text-blue-400">🖥️</span>}
          </div>
          {isRecording && (
            <div className="absolute top-2 right-2 bg-red-600 text-white px-2 py-1 rounded text-sm flex items-center space-x-1">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
              <span>REC</span>
            </div>
          )}
        </div>

        {/* Remote Videos */}
        {participants.map((participantId) => (
          <div key={participantId} className="relative bg-gray-800 rounded-lg overflow-hidden">
            <video
              ref={remoteVideoRefs.current[participantId]}
              autoPlay
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-2 left-2 bg-black bg-opacity-70 text-white px-3 py-1 rounded-lg">
              Participant {participantId}
            </div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-80 text-white p-4 z-10">
        <div className="flex justify-center items-center space-x-4">
          {/* Audio Control */}
          <button
            onClick={toggleMute}
            className={`px-4 py-3 rounded-full transition-colors ${
              isMuted
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-gray-600 hover:bg-gray-700'
            }`}
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? '🔇' : '🎤'}
          </button>

          {/* Video Control */}
          <button
            onClick={toggleVideo}
            className={`px-4 py-3 rounded-full transition-colors ${
              isVideoOff
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-gray-600 hover:bg-gray-700'
            }`}
            title={isVideoOff ? 'Turn on camera' : 'Turn off camera'}
          >
            {isVideoOff ? '📷' : '📹'}
          </button>

          {/* Screen Share */}
          <button
            onClick={toggleScreenShare}
            className={`px-4 py-3 rounded-full transition-colors ${
              isScreenSharing
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-600 hover:bg-gray-700'
            }`}
            title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
          >
            🖥️
          </button>

          {/* Recording */}
          <button
            onClick={toggleRecording}
            className={`px-4 py-3 rounded-full transition-colors ${
              isRecording
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-gray-600 hover:bg-gray-700'
            }`}
            title={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isRecording ? '⏹️' : '⏺️'}
          </button>

          {/* End Call */}
          <button
            onClick={endCall}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded-full transition-colors font-semibold"
            title="End call"
          >
            📞 End
          </button>
        </div>
      </div>
    </div>
  );
};

export default VideoCall;
