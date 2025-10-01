import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Icon } from '../atoms';
import NotificationHistory from './NotificationHistory';

const NotificationSystem = ({
  maxNotifications = 5,
  defaultDuration = 5000,
  position = 'top-right',
  enableSound = true,
  className = '',
  ...props
}) => {
  const [notifications, setNotifications] = useState([]);
  const [soundEnabled, setSoundEnabled] = useState(enableSound);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);

  const notificationTypes = {
    success: {
      icon: 'check',
      color: 'green',
      sound: 'success'
    },
    error: {
      icon: 'x',
      color: 'red',
      sound: 'error'
    },
    warning: {
      icon: 'alertTriangle',
      color: 'yellow',
      sound: 'warning'
    },
    info: {
      icon: 'info',
      color: 'blue',
      sound: 'info'
    },
    message: {
      icon: 'messageSquare',
      color: 'purple',
      sound: 'message'
    }
  };

  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
    'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2'
  };

  // Add notification function
  const addNotification = useCallback((notification) => {
    const id = Date.now() + Math.random();
    const newNotification = {
      id,
      type: notification.type || 'info',
      title: notification.title,
      message: notification.message,
      duration: notification.duration || defaultDuration,
      persistent: notification.persistent || false,
      actions: notification.actions || [],
      timestamp: new Date(),
      ...notification
    };

    setNotifications(prev => {
      const updated = [newNotification, ...prev];
      // Keep only the most recent notifications
      return updated.slice(0, maxNotifications);
    });

    // Play sound if enabled
    if (soundEnabled && newNotification.type) {
      playNotificationSound(newNotification.type);
    }

    // Auto-remove non-persistent notifications
    if (!newNotification.persistent && newNotification.duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, newNotification.duration);
    }

    return id;
  }, [defaultDuration, maxNotifications, soundEnabled]);

  // Remove notification function
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  // Clear all notifications
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Play notification sound
  const playNotificationSound = (type) => {
    if (!soundEnabled) return;

    try {
      // Create audio context for sound generation
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      // Different frequencies for different notification types
      const frequencies = {
        success: [523, 659, 784], // C, E, G
        error: [220, 185], // A, F#
        warning: [440, 554], // A, C#
        info: [523, 659], // C, E
        message: [659, 523] // E, C
      };

      const freq = frequencies[type] || frequencies.info;
      
      oscillator.frequency.setValueAtTime(freq[0], audioContext.currentTime);
      if (freq[1]) {
        oscillator.frequency.setValueAtTime(freq[1], audioContext.currentTime + 0.1);
      }

      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } catch (error) {
      console.warn('Failed to play notification sound:', error);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/notifications');
      const data = await response.json();
      setHistory(data.notifications);
    } catch (error) {
      console.error('Failed to fetch notification history:', error);
    }
  };

  const toggleHistory = () => {
    if (!showHistory) {
      fetchHistory();
    }
    setShowHistory(!showHistory);
  };

  // Expose functions globally for use by other components
  useEffect(() => {
    window.showNotification = addNotification;
    window.removeNotification = removeNotification;
    window.clearNotifications = clearAll;

    return () => {
      delete window.showNotification;
      delete window.removeNotification;
      delete window.clearNotifications;
    };
  }, [addNotification, removeNotification, clearAll]);

  // Listen for WebSocket notifications
  useEffect(() => {
    const handleWebSocketMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'notification') {
          addNotification({
            type: data.notificationType || 'info',
            title: data.title,
            message: data.message,
            duration: data.duration,
            persistent: data.persistent
          });
        }
      } catch (error) {
        // Not a JSON message, ignore
      }
    };

    // Add event listener for custom notification events
    window.addEventListener('websocket-message', handleWebSocketMessage);
    
    return () => {
      window.removeEventListener('websocket-message', handleWebSocketMessage);
    };
  }, [addNotification]);

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (seconds < 60) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return timestamp.toLocaleDateString();
  };

  const renderHistoryModal = () => {
    if (!showHistory) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-lg w-full">
          <NotificationHistory notifications={history} />
          <button
            onClick={toggleHistory}
            className="mt-4 text-sm text-blue-600 hover:text-blue-800"
          >
            Close
          </button>
        </div>
      </div>
    );
  };

  return (
    <>
      <div 
        className={`fixed ${positionClasses[position]} z-50 space-y-2 ${className}`}
        {...props}
      >
        {/* Clear All Button */}
        {notifications.length > 1 && (
          <div className="flex justify-end mb-2">
            <button
              onClick={clearAll}
              className="text-xs text-gray-500 hover:text-gray-700 bg-white rounded-full px-2 py-1 shadow-sm border"
            >
              Clear All
            </button>
          </div>
        )}

        {/* Notifications */}
        {notifications.map((notification) => {
          const typeConfig = notificationTypes[notification.type] || notificationTypes.info;
          
          return (
            <div
              key={notification.id}
              className={`
                bg-white border-l-4 border-${typeConfig.color}-500 rounded-lg shadow-lg 
                max-w-sm w-full p-4 transform transition-all duration-300 ease-in-out
                hover:shadow-xl animate-slide-in-right
              `}
            >
              <div className="flex items-start space-x-3">
                {/* Icon */}
                <div className={`flex-shrink-0 w-6 h-6 rounded-full bg-${typeConfig.color}-100 flex items-center justify-center`}>
                  <Icon 
                    name={typeConfig.icon} 
                    size="sm" 
                    className={`text-${typeConfig.color}-600`}
                  />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {notification.title && (
                    <h4 className="text-sm font-semibold text-gray-900 mb-1">
                      {notification.title}
                    </h4>
                  )}
                  
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {notification.message}
                  </p>

                  {/* Actions */}
                  {notification.actions && notification.actions.length > 0 && (
                    <div className="flex items-center space-x-2 mt-3">
                      {notification.actions.map((action, index) => (
                        <button
                          key={index}
                          onClick={() => {
                            action.handler();
                            if (action.dismissOnClick !== false) {
                              removeNotification(notification.id);
                            }
                          }}
                          className={`
                            text-xs px-3 py-1 rounded-md font-medium transition-colors
                            ${action.primary 
                              ? `bg-${typeConfig.color}-600 text-white hover:bg-${typeConfig.color}-700`
                              : `text-${typeConfig.color}-600 hover:bg-${typeConfig.color}-50`
                            }
                          `}
                        >
                          {action.label}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Timestamp */}
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-500">
                      {formatTimeAgo(notification.timestamp)}
                    </span>
                    
                    {/* Progress bar for timed notifications */}
                    {!notification.persistent && notification.duration > 0 && (
                      <div className="w-16 h-1 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className={`h-full bg-${typeConfig.color}-500 rounded-full animate-progress`}
                          style={{
                            animation: `progress ${notification.duration}ms linear forwards`
                          }}
                        ></div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Close Button */}
                <button
                  onClick={() => removeNotification(notification.id)}
                  className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <Icon name="x" size="sm" />
                </button>
              </div>
            </div>
          );
        })}

        {/* Sound Toggle and History Button */}
        <div className="flex justify-end space-x-2">
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className={`
              p-2 rounded-full transition-colors text-xs
              ${soundEnabled 
                ? 'bg-blue-100 text-blue-600 hover:bg-blue-200' 
                : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
              }
            `}
            title={soundEnabled ? 'Disable sounds' : 'Enable sounds'}
          >
            <Icon name={soundEnabled ? 'volume-2' : 'volume-x'} size="xs" />
          </button>
          <button
            onClick={toggleHistory}
            className="p-2 rounded-full transition-colors text-xs bg-gray-100 text-gray-600 hover:bg-gray-200"
            title="Notification History"
          >
            <Icon name="history" size="xs" />
          </button>
        </div>

        {/* Custom CSS for animations */}
        <style jsx>{`
          @keyframes slide-in-right {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
          
          @keyframes progress {
            from {
              width: 100%;
            }
            to {
              width: 0%;
            }
          }
          
          .animate-slide-in-right {
            animation: slide-in-right 0.3s ease-out;
          }
          
          .animate-progress {
            animation: progress linear forwards;
          }
        `}</style>
      </div>
      {renderHistoryModal()}
    </>
  );
};

NotificationSystem.propTypes = {
  maxNotifications: PropTypes.number,
  defaultDuration: PropTypes.number,
  position: PropTypes.oneOf([
    'top-right', 'top-left', 'bottom-right', 
    'bottom-left', 'top-center', 'bottom-center'
  ]),
  enableSound: PropTypes.bool,
  className: PropTypes.string
};

export default NotificationSystem;