import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from './LoginPage';
import { useAuth } from '../../hooks/useAuth';
import { useVerification } from '../../hooks/useVerification';
import { useNotification } from '../../contexts/NotificationContext';

// Mock hooks
jest.mock('../../hooks/useAuth');
jest.mock('../../hooks/useVerification');
jest.mock('../../contexts/NotificationContext');

describe('LoginPage', () => {
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

  test('renders login form', () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('validates form inputs', async () => {
    render(<LoginPage />);
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
  });

  test('calls login and starts verification on successful login', async () => {
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

  test('shows error notification on login failure', async () => {
    mockLogin.mockResolvedValue({ success: false, error: 'Invalid credentials' });

    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpassword' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith('Invalid credentials', 'error');
    });
  });

  test('shows verification error notification', () => {
    useVerification.mockReturnValue({
      verificationStatus: null,
      verificationError: 'Verification failed',
      startVerification: jest.fn(),
      stopVerification: jest.fn(),
      isVerifying: false,
    });

    render(<LoginPage />);
    expect(mockAddNotification).toHaveBeenCalledWith('Verification error: Verification failed', 'error');
  });
});
