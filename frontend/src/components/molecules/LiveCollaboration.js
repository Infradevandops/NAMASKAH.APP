import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { Icon } from '../atoms';
import TypingIndicator from './TypingIndicator';
import { useVerification } from '../../hooks/useVerification';

const LiveCollaboration = ({
  documentId,
  wsUrl = 'ws://localhost:8000/ws/collaboration',
  currentUser,
  onContentChange,
  onUserJoin,
  onUserLeave,
  showCursors = true,
  showPresence = true,
  className = '',
  ...props
}) => {
  const [connectedUsers, setConnectedUsers] = useState([]);
  const [userCursors, setUserCursors] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const [wsConnection, setWsConnection] = useState(null);
  const [documentContent, setDocumentContent] = useState('');
  const [localChanges, setLocalChanges] = useState([]);
  const contentRef = useRef(null);

  // Use verification hook for status indicators
  const { verificationStatus, isVerifying } = useVerification();

  const userColors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', 
    '#8b5cf6', '#06b6d4', '#f97316', '#84cc16'
  ];

  useEffect(() => {
    if (documentId && currentUser) {
      connectToDocument();
    }

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [documentId, currentUser]);

  const connectToDocument = () => {
    try {
      const ws = new WebSocket(`${wsUrl}/${documentId}`);

      ws.onopen = () => {
        setIsConnected(true);
        
        // Join document session
        ws.send(JSON.stringify({
          type: 'join_document',
          documentId,
          user: currentUser
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Failed to parse collaboration message:', error);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setConnectedUsers([]);
        setUserCursors({});
      };

      ws.onerror = (error) => {
        console.error('Collaboration WebSocket error:', error);
        setIsConnected(false);
      };

      setWsConnection(ws);
    } catch (error) {
      console.error('Failed to connect to collaboration service:', error);
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'user_joined':
        handleUserJoined(data.user);
        break;
      case 'user_left':
        handleUserLeft(data.user);
        break;
      case 'users_list':
        setConnectedUsers(data.users || []);
        break;
      case 'content_change':
        handleRemoteContentChange(data);
        break;
      case 'cursor_position':
        handleCursorUpdate(data);
        break;
      case 'document_content':
        setDocumentContent(data.content || '');
        break;
      default:
        console.log('Unknown collaboration message type:', data.type);
    }
  };

  const handleUserJoined = (user) => {
    setConnectedUsers(prev => {
      const exists = prev.find(u => u.id === user.id);
      if (!exists) {
        const newUsers = [...prev, { ...user, color: getUserColor(user.id) }];
        if (onUserJoin) onUserJoin(user);
        return newUsers;
      }
      return prev;
    });
  };

  const handleUserLeft = (user) => {
    setConnectedUsers(prev => {
      const filtered = prev.filter(u => u.id !== user.id);
      if (onUserLeave) onUserLeave(user);
      return filtered;
    });
    
    setUserCursors(prev => {
      const updated = { ...prev };
      delete updated[user.id];
      return updated;
    });
  };

  const handleRemoteContentChange = (data) => {
    // Apply operational transformation to resolve conflicts
    const transformedChange = applyOperationalTransform(data.change, localChanges);
    
    if (transformedChange) {
      setDocumentContent(prev => applyChange(prev, transformedChange));
      if (onContentChange) {
        onContentChange(transformedChange, data.user);
      }
    }
  };

  const handleCursorUpdate = (data) => {
    if (data.user.id !== currentUser.id) {
      setUserCursors(prev => ({
        ...prev,
        [data.user.id]: {
          position: data.position,
          selection: data.selection,
          user: data.user,
          timestamp: Date.now()
        }
      }));
    }
  };

  const getUserColor = (userId) => {
    const hash = userId.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return userColors[Math.abs(hash) % userColors.length];
  };

  const sendContentChange = (change) => {
    if (wsConnection && isConnected) {
      const changeData = {
        type: 'content_change',
        documentId,
        change,
        user: currentUser,
        timestamp: Date.now()
      };

      wsConnection.send(JSON.stringify(changeData));
      setLocalChanges(prev => [...prev, change]);
    }
  };

  const sendCursorPosition = (position, selection = null) => {
    if (wsConnection && isConnected) {
      wsConnection.send(JSON.stringify({
        type: 'cursor_position',
        documentId,
        position,
        selection,
        user: currentUser,
        timestamp: Date.now()
      }));
    }
  };

  // Operational Transform implementation (simplified)
  const applyOperationalTransform = (remoteChange, localChanges) => {
    // This is a simplified OT implementation
    // In production, you'd use a proper OT library like ShareJS or Yjs
    let transformedChange = { ...remoteChange };
    
    localChanges.forEach(localChange => {
      if (localChange.timestamp > remoteChange.timestamp) {
        // Transform the remote change against local changes
        if (localChange.type === 'insert' && remoteChange.type === 'insert') {
          if (localChange.position <= remoteChange.position) {
            transformedChange.position += localChange.content.length;
          }
        } else if (localChange.type === 'delete' && remoteChange.type === 'insert') {
          if (localChange.position < remoteChange.position) {
            transformedChange.position -= localChange.length;
          }
        }
      }
    });

    return transformedChange;
  };

  const applyChange = (content, change) => {
    switch (change.type) {
      case 'insert':
        return content.slice(0, change.position) + 
               change.content + 
               content.slice(change.position);
      case 'delete':
        return content.slice(0, change.position) + 
               content.slice(change.position + change.length);
      case 'replace':
        return content.slice(0, change.position) + 
               change.content + 
               content.slice(change.position + change.length);
      default:
        return content;
    }
  };

  const handleContentInput = (event) => {
    const newContent = event.target.value;
    const oldContent = documentContent;
    
    // Calculate the change
    const change = calculateChange(oldContent, newContent);
    if (change) {
      setDocumentContent(newContent);
      sendContentChange(change);
    }
  };

  const calculateChange = (oldContent, newContent) => {
    // Simple diff calculation
    if (oldContent === newContent) return null;

    const oldLength = oldContent.length;
    const newLength = newContent.length;

    // Find the first difference
    let start = 0;
    while (start < Math.min(oldLength, newLength) && 
           oldContent[start] === newContent[start]) {
      start++;
    }

    // Find the last difference
    let oldEnd = oldLength;
    let newEnd = newLength;
    while (oldEnd > start && newEnd > start && 
           oldContent[oldEnd - 1] === newContent[newEnd - 1]) {
      oldEnd--;
      newEnd--;
    }

    const deletedLength = oldEnd - start;
    const insertedContent = newContent.slice(start, newEnd);

    if (deletedLength > 0 && insertedContent.length > 0) {
      return {
        type: 'replace',
        position: start,
        length: deletedLength,
        content: insertedContent,
        timestamp: Date.now()
      };
    } else if (deletedLength > 0) {
      return {
        type: 'delete',
        position: start,
        length: deletedLength,
        timestamp: Date.now()
      };
    } else if (insertedContent.length > 0) {
      return {
        type: 'insert',
        position: start,
        content: insertedContent,
        timestamp: Date.now()
      };
    }

    return null;
  };

  const handleSelectionChange = () => {
    if (contentRef.current) {
      const selection = window.getSelection();
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const position = range.startOffset;
        const selectionEnd = range.endOffset;
        
        sendCursorPosition(position, 
          position !== selectionEnd ? { start: position, end: selectionEnd } : null
        );
      }
    }
  };

  const UserPresence = () => (
    <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
      <Icon name="users" size="sm" className="text-gray-500" />
      <span className="text-sm text-gray-600">
        {connectedUsers.length} user{connectedUsers.length !== 1 ? 's' : ''} online
      </span>
      
      <div className="flex -space-x-1">
        {connectedUsers.slice(0, 5).map((user) => (
          <div
            key={user.id}
            className="w-6 h-6 rounded-full border-2 border-white flex items-center justify-center text-xs font-medium text-white"
            style={{ backgroundColor: user.color }}
            title={user.name}
          >
            {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </div>
        ))}
        
        {connectedUsers.length > 5 && (
          <div className="w-6 h-6 rounded-full border-2 border-white bg-gray-500 flex items-center justify-center text-xs font-medium text-white">
            +{connectedUsers.length - 5}
          </div>
        )}
      </div>
    </div>
  );

  const CursorOverlay = () => (
    <div className="absolute inset-0 pointer-events-none">
      {Object.values(userCursors).map((cursor) => (
        <div
          key={cursor.user.id}
          className="absolute"
          style={{
            left: `${cursor.position * 8}px`, // Approximate character width
            top: '0px',
            borderLeft: `2px solid ${cursor.user.color}`,
            height: '20px',
            animation: 'blink 1s infinite'
          }}
        >
          <div
            className="absolute -top-6 left-0 px-2 py-1 text-xs text-white rounded whitespace-nowrap"
            style={{ backgroundColor: cursor.user.color }}
          >
            {cursor.user.name}
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className={`space-y-4 ${className}`} {...props}>
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {showPresence && connectedUsers.length > 0 && <UserPresence />}
      </div>

      {/* Verification Status */}
      <div className="flex items-center space-x-2 p-2 bg-blue-50 border border-blue-300 rounded">
        <Icon name="shield" size="sm" className="text-blue-500" />
        <span className="text-sm text-blue-700">Verification:</span>
        {isVerifying ? (
          <span className="inline-block px-2 py-1 text-xs font-semibold text-yellow-800 bg-yellow-200 rounded-full">
            Verifying...
          </span>
        ) : verificationStatus ? (
          <span
            className={`inline-block px-2 py-1 text-xs font-semibold rounded-full ${
              verificationStatus === 'completed'
                ? 'text-green-800 bg-green-200'
                : verificationStatus === 'failed'
                ? 'text-red-800 bg-red-200'
                : 'text-gray-800 bg-gray-200'
            }`}
          >
            {verificationStatus}
          </span>
        ) : (
          <span className="text-gray-500 text-xs">No active verification</span>
        )}
      </div>

      {/* Collaborative Editor */}
      <div className="relative">
        <textarea
          ref={contentRef}
          value={documentContent}
          onChange={handleContentInput}
          onSelect={handleSelectionChange}
          onKeyUp={handleSelectionChange}
          onClick={handleSelectionChange}
          className="w-full h-64 p-4 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          placeholder="Start typing to collaborate in real-time..."
          disabled={!isConnected}
        />
        
        {showCursors && <CursorOverlay />}
      </div>

      {/* Typing Indicators */}
      <TypingIndicator
        users={connectedUsers.filter(user => user.id !== currentUser.id)}
        showAvatars={true}
        maxDisplayUsers={3}
      />

      {/* Collaboration Stats */}
      {isConnected && (
        <div className="text-xs text-gray-500 space-y-1">
          <div>Document ID: {documentId}</div>
          <div>Local changes: {localChanges.length}</div>
          <div>Connected users: {connectedUsers.length}</div>
        </div>
      )}

      <style jsx>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
};

LiveCollaboration.propTypes = {
  documentId: PropTypes.string.isRequired,
  wsUrl: PropTypes.string,
  currentUser: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    name: PropTypes.string.isRequired,
    avatar: PropTypes.string
  }).isRequired,
  onContentChange: PropTypes.func,
  onUserJoin: PropTypes.func,
  onUserLeave: PropTypes.func,
  showCursors: PropTypes.bool,
  showPresence: PropTypes.bool,
  className: PropTypes.string
};

export default LiveCollaboration;