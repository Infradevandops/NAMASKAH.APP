import React from 'react';

const NotificationHistory = ({ notifications }) => {
  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-2">Notification History</h3>
      <ul className="divide-y divide-gray-200">
        {notifications.map(notification => (
          <li key={notification.id} className="py-2">
            <p className="text-sm font-medium text-gray-900">{notification.title}</p>
            <p className="text-sm text-gray-500">{notification.message}</p>
            <p className="text-xs text-gray-400 mt-1">{new Date(notification.timestamp).toLocaleString()}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default NotificationHistory;
