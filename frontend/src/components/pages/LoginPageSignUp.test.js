import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import LoginPage from './LoginPage';
import { BrowserRouter } from 'react-router-dom';

describe('LoginPage Sign Up and Social Login', () => {
  beforeEach(() => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );
  });

  test('allows user to switch to sign up form', () => {
    const signUpLink = screen.getByText(/sign up/i);
    fireEvent.click(signUpLink);
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  test('allows user to sign up with email and password', () => {
    const signUpLink = screen.getByText(/sign up/i);
    fireEvent.click(signUpLink);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const createAccountButton = screen.getByRole('button', { name: /create account/i });

    fireEvent.change(emailInput, { target: { value: 'newuser@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'newpassword123' } });
    fireEvent.click(createAccountButton);

    // Add assertions for expected behavior after sign up
  });

  test('renders social login buttons', () => {
    expect(screen.getByRole('button', { name: /sign in with google/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in with facebook/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in with instagram/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in with x/i })).toBeInTheDocument();
  });

  // Additional tests for social login flows can be added here
});
