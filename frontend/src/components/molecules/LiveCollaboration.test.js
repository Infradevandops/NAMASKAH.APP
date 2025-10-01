import React from 'react';
import { render, screen, act } from '@testing-library/react';
import LiveCollaboration from './LiveCollaboration';

describe('LiveCollaboration', () => {
  let mockWebSocket;

  beforeEach(() => {
    mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
    };
    global.WebSocket = jest.fn(() => mockWebSocket);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders connection status and verification status', () => {
    render(
      <LiveCollaboration
        documentId="doc1"
        currentUser={{ id: 'user1', name: 'User One' }}
      />
    );

    expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
    expect(screen.getByText(/no active verification/i)).toBeInTheDocument();
  });

  test('connects to WebSocket and handles user join/leave', () => {
    render(
      <LiveCollaboration
        documentId="doc1"
        currentUser={{ id: 'user1', name: 'User One' }}
      />
    );

    act(() => {
      mockWebSocket.onopen();
    });

    expect(screen.getByText(/connected/i)).toBeInTheDocument();

    act(() => {
      mockWebSocket.onmessage({
        data: JSON.stringify({ type: 'user_joined', user: { id: 'user2', name: 'User Two' } }),
      });
    });

    expect(screen.getByText(/2 users online/i)).toBeInTheDocument();

    act(() => {
      mockWebSocket.onmessage({
        data: JSON.stringify({ type: 'user_left', user: { id: 'user2', name: 'User Two' } }),
      });
    });

    expect(screen.getByText(/1 user online/i)).toBeInTheDocument();
  });

  test('handles content change and cursor position messages', () => {
    render(
      <LiveCollaboration
        documentId="doc1"
        currentUser={{ id: 'user1', name: 'User One' }}
      />
    );

    act(() => {
      mockWebSocket.onopen();
    });

    act(() => {
      mockWebSocket.onmessage({
        data: JSON.stringify({ type: 'document_content', content: 'Hello' }),
      });
    });

    expect(screen.getByPlaceholderText(/start typing/i).value).toBe('Hello');

    act(() => {
      mockWebSocket.onmessage({
        data: JSON.stringify({
          type: 'cursor_position',
          user: { id: 'user2', name: 'User Two', color: '#3b82f6' },
          position: 3,
          selection: null,
        }),
      });
    });

    // Cursor overlay presence can be checked by user name display
    expect(screen.getByText('User Two')).toBeInTheDocument();
  });
});
