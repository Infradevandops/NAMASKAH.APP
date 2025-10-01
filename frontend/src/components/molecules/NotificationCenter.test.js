import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NotificationCenter from './NotificationCenter';

const mockNotifications = [
  {
    id: 1,
    title: 'Success',
    message: 'Operation completed successfully',
    type: 'success',
    timestamp: new Date().toISOString(),
    read: false
  },
  {
    id: 2,
    title: 'Error',
    message: 'Something went wrong',
    type: 'error',
    timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    read: true
  },
  {
    id: 3,
    title: 'Verification Complete',
    message: 'Your verification has been processed',
    type: 'verification',
    timestamp: new Date(Date.now() - 600000).toISOString(), // 10 minutes ago
    read: false
  }
];

describe('NotificationCenter', () => {
  const defaultProps = {
    notifications: mockNotifications,
    onMarkAsRead: jest.fn(),
    onMarkAllAsRead: jest.fn(),
    onDeleteNotification: jest.fn(),
    onClearAll: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render notification bell with unread count', () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    expect(bellButton).toBeInTheDocument();

    // Should show unread count badge
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('should open notification dropdown when bell is clicked', async () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    fireEvent.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });
  });

  it('should filter notifications correctly', async () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    fireEvent.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });

    // Test "Unread" filter
    const unreadFilter = screen.getByText('Unread');
    fireEvent.click(unreadFilter);

    expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
    expect(screen.getByText('Your verification has been processed')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();

    // Test "Read" filter
    const readFilter = screen.getByText('Read');
    fireEvent.click(readFilter);

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.queryByText('Operation completed successfully')).not.toBeInTheDocument();

    // Test "All" filter
    const allFilter = screen.getByText('All');
    fireEvent.click(allFilter);

    expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Your verification has been processed')).toBeInTheDocument();
  });

  it('should mark notification as read when clicked', async () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    fireEvent.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
    });

    const markAsReadButton = screen.getByText('Mark as read');
    fireEvent.click(markAsReadButton);

    expect(defaultProps.onMarkAsRead).toHaveBeenCalledWith(1);
  });

  it('should delete notification when delete button is clicked', async () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    fireEvent.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByLabelText('Delete notification');
    fireEvent.click(deleteButtons[0]);

    expect(defaultProps.onDeleteNotification).toHaveBeenCalledWith(1);
  });

  it('should mark all notifications as read', async () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    fireEvent.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText('Mark all read')).toBeInTheDocument();
    });

    const markAllReadButton = screen.getByText('Mark all read');
    fireEvent.click(markAllReadButton);

    expect(defaultProps.onMarkAllAsRead).toHaveBeenCalled();
  });

  it('should clear all notifications', async () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    fireEvent.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText('Clear all')).toBeInTheDocument();
    });

    const clearAllButton = screen.getByText('Clear all');
    fireEvent.click(clearAllButton);

    expect(defaultProps.onClearAll).toHaveBeenCalled();
  });

  it('should display correct notification types with appropriate icons', async () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    fireEvent.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
    });

    // Check that different notification types are displayed
    expect(screen.getByText('Success')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Verification Complete')).toBeInTheDocument();
  });

  it('should format timestamps correctly', async () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    fireEvent.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
    });

    // Should show relative time (Just now, 10m ago, 1h ago)
    expect(screen.getByText(/just now|10m ago|1h ago/i)).toBeInTheDocument();
  });

  it('should show empty state when no notifications', () => {
    render(<NotificationCenter {...defaultProps} notifications={[]} />);

    const bellButton = screen.getByRole('button', { name: /notifications/i });
    fireEvent.click(bellButton);

    expect(screen.getByText('No notifications')).toBeInTheDocument();
  });

  it('should close dropdown when clicking outside', async () => {
    render(<NotificationCenter {...defaultProps} />);

    const bellButton = screen.getByRole('button', { name: /notifications \(2 unread\)/i });
    fireEvent.click(bellButton);

    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });

    // Click outside (on document body)
    fireEvent.click(document.body);

    await waitFor(() => {
      expect(screen.queryByText('Notifications')).not.toBeInTheDocument();
    });
  });
});
