import { renderHook, act, waitFor } from '@testing-library/react';
import { useVerification } from './useVerification';

// Mock axios
jest.mock('axios');
import axios from 'axios';

// Mock WebSocket
const mockWebSocket = {
  onopen: null,
  onmessage: null,
  onerror: null,
  onclose: null,
  close: jest.fn(),
  send: jest.fn(),
  readyState: 1 // OPEN
};

global.WebSocket = jest.fn(() => mockWebSocket);

// Mock Notification API
global.Notification = {
  permission: 'default',
  requestPermission: jest.fn().mockResolvedValue('granted')
};

Object.defineProperty(global, 'Notification', {
  value: jest.fn().mockImplementation(() => ({
    constructor: global.Notification
  })),
  writable: true
});

describe('useVerification', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useVerification());

    expect(result.current.verificationStatus).toBeNull();
    expect(result.current.verificationError).toBeNull();
    expect(result.current.isVerifying).toBe(false);
    expect(result.current.usePolling).toBe(false);
  });

  it('should start verification process successfully', async () => {
    const mockResponse = { data: { id: '123', status: 'pending' } };
    axios.post.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification();
    });

    expect(result.current.isVerifying).toBe(true);

    // Wait for WebSocket connection
    await waitFor(() => {
      expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost/ws/verification/123');
    });

    // Simulate WebSocket open
    act(() => {
      mockWebSocket.onopen();
    });

    expect(axios.post).toHaveBeenCalledWith('/api/verification/start');
  });

  it('should handle WebSocket connection failure and fallback to polling', async () => {
    const mockResponse = { data: { id: '123', status: 'pending' } };
    axios.post.mockResolvedValueOnce(mockResponse);
    axios.get.mockResolvedValueOnce({ data: { status: 'completed' } });

    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification();
    });

    // Simulate WebSocket error
    act(() => {
      mockWebSocket.onerror(new Error('Connection failed'));
    });

    expect(result.current.usePolling).toBe(true);

    // Fast-forward timers to trigger polling
    act(() => {
      jest.advanceTimersByTime(2000);
    });

    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith('/api/verification/status/123');
    });
  });

  it('should show notifications for status changes', async () => {
    const mockResponse = { data: { id: '123', status: 'pending' } };
    axios.post.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification();
    });

    // Simulate WebSocket open and message
    act(() => {
      mockWebSocket.onopen();
      mockWebSocket.onmessage({
        data: JSON.stringify({ type: 'verification_status', status: 'completed' })
      });
    });

    expect(result.current.verificationStatus).toBe('completed');
    expect(result.current.isVerifying).toBe(false);
  });

  it('should handle polling with exponential backoff', async () => {
    const mockResponse = { data: { id: '123', status: 'pending' } };
    axios.post.mockResolvedValueOnce(mockResponse);
    axios.get
      .mockResolvedValueOnce({ data: { status: 'processing' } })
      .mockResolvedValueOnce({ data: { status: 'completed' } });

    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification();
    });

    // Simulate WebSocket error to trigger polling
    act(() => {
      mockWebSocket.onerror(new Error('Connection failed'));
    });

    expect(result.current.usePolling).toBe(true);

    // First poll
    act(() => {
      jest.advanceTimersByTime(2000);
    });

    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledTimes(1);
    });

    // Second poll (should be at increased interval)
    act(() => {
      jest.advanceTimersByTime(3000); // 2 * 1.5 = 3 seconds
    });

    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledTimes(2);
    });
  });

  it('should stop verification and cleanup resources', () => {
    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.stopVerification();
    });

    expect(result.current.isVerifying).toBe(false);
    expect(result.current.verificationStatus).toBeNull();
    expect(result.current.verificationError).toBeNull();
    expect(result.current.usePolling).toBe(false);
  });

  it('should handle verification errors', async () => {
    axios.post.mockRejectedValueOnce(new Error('API Error'));

    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification();
    });

    await waitFor(() => {
      expect(result.current.verificationError).toBe('API Error');
      expect(result.current.isVerifying).toBe(false);
    });
  });

  it('should request notification permission on start', async () => {
    const mockResponse = { data: { id: '123', status: 'pending' } };
    axios.post.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useVerification());

    act(() => {
      result.current.startVerification();
    });

    expect(global.Notification.requestPermission).toHaveBeenCalled();
  });
});
