import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import axios from 'axios';
import VerificationAnalytics from './VerificationAnalytics';

jest.mock('axios');

describe('VerificationAnalytics', () => {
  test('renders loading spinner initially', () => {
    axios.get.mockReturnValue(new Promise(() => {})); // never resolves
    render(<VerificationAnalytics />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders bar chart after data fetch', async () => {
    const mockData = [
      { period: '2023-01', success_count: 10, failure_count: 2 },
      { period: '2023-02', success_count: 15, failure_count: 3 },
    ];
    axios.get.mockResolvedValue({ data: mockData });

    render(<VerificationAnalytics />);

    await waitFor(() => {
      expect(screen.getByText('Verification Analytics')).toBeInTheDocument();
      // Chart rendering is tested by presence of canvas element
      expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
    });
  });

  test('renders error message on fetch failure', async () => {
    axios.get.mockRejectedValue(new Error('Network error'));

    render(<VerificationAnalytics />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });
});
