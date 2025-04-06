import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock useAuth hook before importing the component
jest.mock('../../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

// Mock next/link
jest.mock('next/link', () => {
  return ({ children }) => children;
});

// Now import the components and hooks
import { LoginForm } from '../LoginForm';
import { useAuth } from '../../hooks/useAuth';

describe('LoginForm', () => {
  const loginMock = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup auth context mock
    (useAuth as jest.Mock).mockReturnValue({
      authState: {
        isAuthenticated: false,
        isLoading: false,
        error: null,
        user: null,
      },
      login: loginMock,
    });
  });
  
  it('should render the login form', () => {
    render(<LoginForm />);
    
    // Form title
    expect(screen.getByText('Log In', { selector: 'h2' })).toBeInTheDocument();
    
    // Form fields
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    
    // Submit button
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
  });
  
  it('should submit valid form data', async () => {
    render(<LoginForm />);
    
    // Enter valid email
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'user@example.com' },
    });
    
    // Enter valid password
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /log in/i }));
    
    // Wait for form submission
    await waitFor(() => {
      // Login should be called with correct data
      expect(loginMock).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: 'password123',
      });
    });
  });
  
  it('should display error message from auth state', () => {
    // Mock auth state with error
    (useAuth as jest.Mock).mockReturnValue({
      authState: {
        isAuthenticated: false,
        isLoading: false,
        error: 'Invalid credentials',
        user: null,
      },
      login: loginMock,
    });
    
    render(<LoginForm />);
    
    // Error message should be displayed
    expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
  });
  
  it('should display loading state during authentication', () => {
    // Mock loading auth state
    (useAuth as jest.Mock).mockReturnValue({
      authState: {
        isAuthenticated: false,
        isLoading: true,
        error: null,
        user: null,
      },
      login: loginMock,
    });
    
    render(<LoginForm />);
    
    // Submit button should be disabled and show loading
    const submitButton = screen.getByRole('button');
    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveTextContent('Loading...');
  });
});