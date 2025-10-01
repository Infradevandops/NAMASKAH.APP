import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import PropTypes from 'react';

const NotificationContext = createContext();

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  // Add a new notification
  const addNotification = useCallback((message, type = 'info', title = null, duration = 5000) => {
    const id = Date.now() + Math.random();
    const notification = {
      id,
      title: title || getDefaultTitle(type),
      message,
      type,
      timestamp: new Date().toISOString(),
      read: false,
      duration
    };

    setNotifications(prev => [notification, ...prev]);

    // Auto-remove after duration (if specified)
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, duration);
    }

    return id;
  }, []);

  // Remove a notification
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  // Mark notification as read
  const markAsRead = useCallback((id) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  }, []);

  // Mark all notifications as read
  const markAllAsRead = useCallback(() => {
    setNotifications(prev =>
      prev.map(notification => ({ ...notification, read: true }))
    );
  }, []);

  // Clear all notifications
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Get unread count
  const getUnreadCount = useCallback(() => {
    return notifications.filter(notification => !notification.read).length;
  }, [notifications]);

  // Get notifications by type
  const getNotificationsByType = useCallback((type) => {
    return notifications.filter(notification => notification.type === type);
  }, [notifications]);

  // Auto-cleanup old notifications (older than 24 hours)
  useEffect(() => {
    const cleanup = () => {
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      setNotifications(prev =>
        prev.filter(notification => new Date(notification.timestamp) > oneDayAgo)
      );
    };

    const interval = setInterval(cleanup, 60 * 60 * 1000); // Check every hour
    return () => clearInterval(interval);
  }, []);

  const value = {
    notifications,
    addNotification,
    removeNotification,
    markAsRead,
    markAllAsRead,
    clearAll,
    getUnreadCount,
    getNotificationsByType
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

// Helper function to get default title based on type
const getDefaultTitle = (type) => {
  const titles = {
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Information',
    verification: 'Verification'
  };
  return titles[type] || 'Notification';
};

NotificationProvider.propTypes = {
  children: PropTypes.node.isRequired
};
