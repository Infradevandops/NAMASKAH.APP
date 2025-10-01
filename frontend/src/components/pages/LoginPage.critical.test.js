import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from './LoginPage';
import { useAuth } from '../../hooks/useAuth';
import { useVerification } from '../../hooks/useVerification';
import { useNotification } from '../../contexts/NotificationContext';

jest.mock('../../hooks/useAuth');
jest.mock('../../hooks/useVerification');
jest.mock('../../contexts/NotificationContext');

describe('LoginPage Critical Path', () => {
  const mockLogin = jest.fn();
  const mockStartVerification = jest.fn();
  const mockAddNotification = jest.fn();

  beforeEach(() => {
    useAuth.mockReturnValue({ login: mockLogin });
    useVerification.mockReturnValue({
      verificationStatus: null,
      verificationError: null,
      startVerification: mockStartVerification,
      stopVerification: jest.fn(),
      isVerifying: false,
    });
    useNotification.mockReturnValue({ addNotification: mockAddNotification });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('successful login triggers verification start', async () => {
    mockLogin.mockResolvedValue({ success: true });

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(mockStartVerification).toHaveBeenCalled();
      expect(mockAddNotification).toHaveBeenCalledWith('Login successful!', 'success');
    });
  });

  test('login failure shows error notification', async () => {
    mockLogin.mockResolvedValue({ success: false, error: 'Invalid credentials' });

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpassword' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith('Invalid credentials', 'error');
    });
  });
});
