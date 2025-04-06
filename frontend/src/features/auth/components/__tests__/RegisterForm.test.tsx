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
import { RegisterForm } from '../RegisterForm';
import { useAuth } from '../../hooks/useAuth';

describe('RegisterForm', () => {
  const registerMock = jest.fn();
  
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
      register: registerMock,
    });
  });
  
  it('should render the registration form', () => {
    render(<RegisterForm />);
    
    // Form title
    expect(screen.getByText('Create an Account')).toBeInTheDocument();
    
    // Form fields
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/organization name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    
    // Submit button
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
  });
  
  it('should submit valid form data without organization', async () => {
    render(<RegisterForm />);
    
    // Fill required fields
    fireEvent.change(screen.getByLabelText(/full name/i), {
      target: { value: 'Test User' },
    });
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'password123' },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'password123' },
    });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /register/i }));
    
    // Wait for form submission
    await waitFor(() => {
      // Register should be called
      expect(registerMock).toHaveBeenCalled();
    });
  });
  
  it('should submit valid form data with organization', async () => {
    render(<RegisterForm />);
    
    // Fill all fields including organization
    fireEvent.change(screen.getByLabelText(/full name/i), {
      target: { value: 'Test User' },
    });
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/organization name/i), {
      target: { value: 'Test Organization' },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'password123' },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'password123' },
    });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /register/i }));
    
    // Wait for form submission
    await waitFor(() => {
      // Register should be called
      expect(registerMock).toHaveBeenCalled();
      
      // Get the arguments
      const calls = registerMock.mock.calls;
      expect(calls.length).toBeGreaterThan(0);
      
      // Check that organization_name is included in the call
      const callData = calls[0][0];
      expect(callData).toHaveProperty('organization_name');
    });
  });
  
  it('should display error message from auth state', () => {
    // Mock auth state with error
    (useAuth as jest.Mock).mockReturnValue({
      authState: {
        isAuthenticated: false,
        isLoading: false,
        error: 'Registration failed',
        user: null,
      },
      register: registerMock,
    });
    
    render(<RegisterForm />);
    
    // Error message should be displayed
    expect(screen.getByText('Registration failed')).toBeInTheDocument();
  });
  
  it('should display loading state during registration', () => {
    // Mock loading auth state
    (useAuth as jest.Mock).mockReturnValue({
      authState: {
        isAuthenticated: false,
        isLoading: true,
        error: null,
        user: null,
      },
      register: registerMock,
    });
    
    render(<RegisterForm />);
    
    // Submit button should be disabled and show loading
    const submitButton = screen.getByRole('button');
    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveTextContent('Loading...');
  });
});