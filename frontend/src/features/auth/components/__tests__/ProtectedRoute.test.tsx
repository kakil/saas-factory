import React from 'react';
import { render, screen } from '@testing-library/react';
import { useRouter } from 'next/router';

// Mock useAuth hook before importing the component
jest.mock('../../hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

// Mock router
jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}));

// Now import the components and hooks
import { ProtectedRoute } from '../ProtectedRoute';
import { useAuth } from '../../hooks/useAuth';

describe('ProtectedRoute', () => {
  const replaceMock = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup router mock
    (useRouter as jest.Mock).mockReturnValue({
      replace: replaceMock,
    });
  });
  
  it('should render children when authenticated', () => {
    // Mock authenticated state
    (useAuth as jest.Mock).mockReturnValue({
      authState: {
        isAuthenticated: true,
        isLoading: false,
        user: { id: 1, name: 'Test User' },
        error: null,
      },
    });
    
    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    );
    
    // Children should be rendered
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    
    // No redirect should occur
    expect(replaceMock).not.toHaveBeenCalled();
  });
  
  it('should show loading indicator when authentication is in progress', () => {
    // Mock loading state
    (useAuth as jest.Mock).mockReturnValue({
      authState: {
        isAuthenticated: false,
        isLoading: true,
        user: null,
        error: null,
      },
    });
    
    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    );
    
    // Loading indicator should be rendered
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    // Protected content should not be rendered
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    
    // No redirect should occur yet (still loading)
    expect(replaceMock).not.toHaveBeenCalled();
  });
  
  it('should redirect to login when not authenticated', () => {
    // Mock unauthenticated state
    (useAuth as jest.Mock).mockReturnValue({
      authState: {
        isAuthenticated: false,
        isLoading: false,
        user: null,
        error: null,
      },
    });
    
    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    );
    
    // Protected content should not be rendered
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    
    // Should redirect to login
    expect(replaceMock).toHaveBeenCalledWith('/auth/login');
  });
  
  it('should redirect to custom path when specified', () => {
    // Mock unauthenticated state
    (useAuth as jest.Mock).mockReturnValue({
      authState: {
        isAuthenticated: false,
        isLoading: false,
        user: null,
        error: null,
      },
    });
    
    render(
      <ProtectedRoute redirectTo="/custom/login">
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    );
    
    // Should redirect to custom path
    expect(replaceMock).toHaveBeenCalledWith('/custom/login');
  });
});