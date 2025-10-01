import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import axios from 'axios';
import VerificationDashboard from './VerificationDashboard';

jest.mock('axios');

describe('VerificationDashboard', () => {
  test('renders loading spinner initially', () => {
    axios.get.mockReturnValue(new Promise(() => {})); // never resolves
    render(<VerificationDashboard />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders verification records after fetch', async () => {
    const mockData = [
      { id: '1', status: 'completed', created_at: '2023-01-01T00:00:00Z', completed_at: '2023-01-01T01:00:00Z' },
      { id: '2', status: 'failed', created_at: '2023-01-02T00:00:00Z', completed_at: null },
    ];
    axios.get.mockResolvedValue({ data: mockData });

    render(<VerificationDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Verification Dashboard')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('failed')).toBeInTheDocument();
    });
  });

  test('renders error message on fetch failure', async () => {
    axios.get.mockRejectedValue(new Error('Network error'));

    render(<VerificationDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  test('renders no records message when empty', async () => {
    axios.get.mockResolvedValue({ data: [] });

    render(<VerificationDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/no verification records found/i)).toBeInTheDocument();
    });
  });
});
