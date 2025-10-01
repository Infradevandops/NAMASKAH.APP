import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import AccountDeactivation from './AccountDeactivation'; // Assuming this component exists
import { BrowserRouter } from 'react-router-dom';

describe('AccountDeactivation', () => {
  beforeEach(() => {
    render(
      <BrowserRouter>
        <AccountDeactivation />
      </BrowserRouter>
    );
  });

  test('renders deactivation confirmation message', () => {
    expect(screen.getByText(/are you sure you want to deactivate your account/i)).toBeInTheDocument();
  });

  test('calls onDeactivate callback when confirm button is clicked', () => {
    const confirmButton = screen.getByRole('button', { name: /deactivate account/i });
    fireEvent.click(confirmButton);
    // Add assertions for expected behavior after deactivation
  });

  test('calls onCancel callback when cancel button is clicked', () => {
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);
    // Add assertions for expected behavior after cancel
  });
});
