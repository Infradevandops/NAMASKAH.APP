import React, { useState, useEffect, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Icon } from '../atoms';
import TypingIndicator from './TypingIndicator';

const RealTimeChat = ({
  conversationId,
  currentUser,
  wsUrl = 'ws://localhost:8000/ws/chat',
  onMessageSent,
  onMessageReceived,
  onUserJoined,
  onUserLeft,
  onTypingStart,
  onTypingStop,
  className = '',
  maxHeight = '400px',
  showOnlineUsers = true,
  ...props
}) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [typingUsers, setTypingUsers] = useState([]);
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    try {
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('Chat WebSocket connected');
        setIsConnected(true);

        // Join conversation
        socket.send(JSON.stringify({
          type: 'join_conversation',
          conversation_id: conversationId,
          user: currentUser
        }));
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      socket.onclose = () => {
        console.log('Chat WebSocket disconnected');
        setIsConnected(false);
        setOnlineUsers([]);
        setTypingUsers([]);
      };

      socket.onerror = (error) => {
        console.error('Chat WebSocket error:', error);
        setIsConnected(false);
      };

      setWs(socket);
    } catch (error) {
      console.error('Failed to connect to chat WebSocket:', error);
    }
  }, [wsUrl, conversationId, currentUser]);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((data) => {
    switch (data.type) {
      case 'message':
        const newMsg = {
          id: data.id || Date.now(),
          content: data.content,
          sender: data.sender,
          timestamp: data.timestamp || new Date().toISOString(),
          messageType: data.message_type || 'CHAT'
        };
        setMessages(prev => [...prev, newMsg]);
        if (onMessageReceived) onMessageReceived(newMsg);
        break;

      case 'user_joined':
        setOnlineUsers(prev => {
          const exists = prev.find(u => u.id === data.user.id);
          if (!exists) {
            const updated = [...prev, data.user];
            if (onUserJoined) onUserJoined(data.user);
            return updated;
          }
          return prev;
        });
        break;

      case 'user_left':
        setOnlineUsers(prev => {
          const filtered = prev.filter(u => u.id !== data.user.id);
          if (onUserLeft) onUserLeft(data.user);
          return filtered;
        });
        break;

      case 'users_online':
        setOnlineUsers(data.users || []);
        break;

      case 'typing_start':
        if (data.user.id !== currentUser.id) {
          setTypingUsers(prev => {
            const exists = prev.find(u => u.id === data.user.id);
            if (!exists) {
              return [...prev, data.user];
            }
            return prev;
          });
        }
        break;

      case 'typing_stop':
        setTypingUsers(prev => prev.filter(u => u.id !== data.user.id));
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }, [currentUser.id, onMessageReceived, onUserJoined, onUserLeft]);

  // Connect on mount
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connectWebSocket, ws]);

  // Send message
  const sendMessage = () => {
    if (!newMessage.trim() || !ws || !isConnected) return;

    const messageData = {
      type: 'send_message',
      conversation_id: conversationId,
      content: newMessage.trim(),
      message_type: 'CHAT',
      timestamp: new Date().toISOString()
    };

    ws.send(JSON.stringify(messageData));

    // Add message to local state immediately for better UX
    const localMessage = {
      id: `local-${Date.now()}`,
      content: newMessage.trim(),
      sender: currentUser,
      timestamp: new Date().toISOString(),
      messageType: 'CHAT',
      isLocal: true
    };

    setMessages(prev => [...prev, localMessage]);
    setNewMessage('');

    // Stop typing indicator
    stopTyping();

    if (onMessageSent) onMessageSent(localMessage);
  };

  // Handle typing
  const startTyping = () => {
    if (!ws || !isConnected) return;

    ws.send(JSON.stringify({
      type: 'typing_start',
      conversation_id: conversationId,
      user: currentUser
    }));

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set timeout to stop typing
    typingTimeoutRef.current = setTimeout(() => {
      stopTyping();
    }, 3000);
  };

  const stopTyping = () => {
    if (!ws || !isConnected) return;

    ws.send(JSON.stringify({
      type: 'typing_stop',
      conversation_id: conversationId,
      user: currentUser
    }));

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }
  };

  // Handle input change with typing indicator
  const handleInputChange = (e) => {
    setNewMessage(e.target.value);

    if (e.target.value.trim()) {
      startTyping();
    } else {
      stopTyping();
    }
  };

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`real-time-chat bg-white rounded-lg shadow-lg border border-gray-200 ${className}`} {...props}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Icon name="comments" size="lg" className="text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900">Chat</h3>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          </div>

          {showOnlineUsers && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Icon name="users" size="sm" />
              <span>{onlineUsers.length} online</span>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div
        className="p-4 overflow-y-auto"
        style={{ maxHeight }}
      >
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <Icon name="comments" size="3x" className="mx-auto mb-3 opacity-50" />
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender.id === currentUser.id ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.sender.id === currentUser.id
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-900'
                  }`}
                >
                  {message.sender.id !== currentUser.id && (
                    <div className="text-xs font-medium text-gray-600 mb-1">
                      {message.sender.name}
                    </div>
                  )}
                  <div className="text-sm">{message.content}</div>
                  <div
                    className={`text-xs mt-1 ${
                      message.sender.id === currentUser.id ? 'text-blue-200' : 'text-gray-500'
                    }`}
                  >
                    {formatTime(message.timestamp)}
                    {message.isLocal && <span className="ml-1">Sending...</span>}
                  </div>
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {typingUsers.length > 0 && (
              <div className="flex justify-start">
                <div className="bg-gray-200 px-4 py-2 rounded-lg">
                  <TypingIndicator
                    users={typingUsers}
                    showAvatars={false}
                    className="text-sm text-gray-600"
                  />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <div className="flex-1">
            <textarea
              value={newMessage}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows="2"
              disabled={!isConnected}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={!newMessage.trim() || !isConnected}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Icon name="paper-plane" size="sm" />
          </button>
        </div>

        {!isConnected && (
          <p className="text-xs text-red-500 mt-2">
            Disconnected from chat. Trying to reconnect...
          </p>
        )}
      </div>
    </div>
  );
};

RealTimeChat.propTypes = {
  conversationId: PropTypes.string.isRequired,
  currentUser: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    name: PropTypes.string.isRequired,
    avatar: PropTypes.string
  }).isRequired,
  wsUrl: PropTypes.string,
  onMessageSent: PropTypes.func,
  onMessageReceived: PropTypes.func,
  onUserJoined: PropTypes.func,
  onUserLeft: PropTypes.func,
  onTypingStart: PropTypes.func,
  onTypingStop: PropTypes.func,
  className: PropTypes.string,
  maxHeight: PropTypes.string,
  showOnlineUsers: PropTypes.bool
};

export default RealTimeChat;
