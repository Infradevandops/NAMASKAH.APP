import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

export function useVerification() {
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [verificationError, setVerificationError] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);

  const [ws, setWs] = useState(null);
  const [usePolling, setUsePolling] = useState(false);
  const pollingIntervalRef = useRef(null);
  const pollingAttemptsRef = useRef(0);
  const maxPollingAttempts = 5;

  // Request notification permission
  const requestNotificationPermission = useCallback(async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  }, []);

  // Show push notification
  const showNotification = useCallback((title, body, icon = '/favicon.ico') => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, {
        body,
        icon,
        tag: 'verification',
        requireInteraction: false
      });
    }
  }, []);

  // Start verification process
  const startVerification = useCallback(async () => {
    setIsVerifying(true);
    setVerificationError(null);
    setUsePolling(false);
    pollingAttemptsRef.current = 0;

    // Request notification permission
    await requestNotificationPermission();

    try {
      // Call API to create a new verification
      const response = await axios.post('/api/verification/start');
      const { id, status } = response.data;
      setVerificationStatus(status);

      // Show initial notification
      showNotification('Verification Started', `Verification ${id} has been initiated`);

      // Try WebSocket connection first
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const socket = new WebSocket(`${protocol}://${window.location.host}/ws/verification/${id}`);

      socket.onopen = () => {
        console.log('WebSocket connected for verification');
        setUsePolling(false);
        // Stop any existing polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.status) {
          const previousStatus = verificationStatus;
          setVerificationStatus(data.status);

          // Show notifications for status changes
          if (data.status !== previousStatus) {
            if (data.status === 'completed') {
              showNotification('Verification Completed', `Verification ${id} completed successfully`);
            } else if (data.status === 'failed') {
              showNotification('Verification Failed', `Verification ${id} failed. Please try again.`);
            }
          }

          if (data.status === 'completed' || data.status === 'failed') {
            setIsVerifying(false);
            socket.close();
          }
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket error, falling back to polling:', error);
        setUsePolling(true);
        startPolling(id);
      };

      socket.onclose = () => {
        console.log('WebSocket closed');
        // If WebSocket closes and we're still verifying, start polling
        if (isVerifying && !usePolling) {
          setUsePolling(true);
          startPolling(id);
        }
      };

      setWs(socket);

      // Set a timeout to fallback to polling if WebSocket doesn't connect
      setTimeout(() => {
        if (socket.readyState !== WebSocket.OPEN && !usePolling) {
          console.log('WebSocket connection timeout, falling back to polling');
          setUsePolling(true);
          startPolling(id);
        }
      }, 5000);

    } catch (error) {
      setVerificationError(error.message || 'Failed to start verification');
      setIsVerifying(false);
      showNotification('Verification Error', 'Failed to start verification process');
    }
  }, [requestNotificationPermission, showNotification, verificationStatus]);

  // Start polling with exponential backoff
  const startPolling = useCallback((id) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    const poll = async () => {
      try {
        const response = await axios.get(`/api/verification/status/${id}`);
        const { status } = response.data;

        const previousStatus = verificationStatus;
        setVerificationStatus(status);

        // Show notifications for status changes
        if (status !== previousStatus) {
          if (status === 'completed') {
            showNotification('Verification Completed', `Verification ${id} completed successfully`);
          } else if (status === 'failed') {
            showNotification('Verification Failed', `Verification ${id} failed. Please try again.`);
          }
        }

        if (status === 'completed' || status === 'failed') {
          setIsVerifying(false);
          stopPolling();
          return;
        }

        pollingAttemptsRef.current = 0; // Reset on successful poll
      } catch (error) {
        console.error('Polling error:', error);
        pollingAttemptsRef.current++;

        if (pollingAttemptsRef.current >= maxPollingAttempts) {
          setVerificationError('Failed to get verification status after multiple attempts');
          setIsVerifying(false);
          stopPolling();
          showNotification('Verification Error', 'Lost connection to verification service');
          return;
        }
      }
    };

    // Initial poll
    poll();

    // Set up interval with exponential backoff
    let interval = 2000; // Start with 2 seconds
    pollingIntervalRef.current = setInterval(() => {
      poll();
      // Increase interval exponentially, max 30 seconds
      interval = Math.min(interval * 1.5, 30000);
    }, interval);
  }, [verificationStatus, showNotification]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  // Stop verification process and cleanup
  const stopVerification = useCallback(() => {
    if (ws) {
      ws.close();
      setWs(null);
    }
    stopPolling();
    setIsVerifying(false);
    setVerificationStatus(null);
    setVerificationError(null);
    setUsePolling(false);
  }, [ws, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
      stopPolling();
    };
  }, [ws, stopPolling]);

  return {
    verificationStatus,
    verificationError,
    isVerifying,
    usePolling,
    startVerification,
    stopVerification,
    showNotification,
  };
}
