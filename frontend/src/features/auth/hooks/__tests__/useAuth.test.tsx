import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { useRouter } from 'next/router';

// Need to mock the API before importing the hooks
jest.mock('../../api', () => ({
  AuthClient: {
    login: jest.fn(),
    register: jest.fn(),
    getCurrentUser: jest.fn(),
    logout: jest.fn(),
    refreshToken: jest.fn(),
    storeTokens: jest.fn(),
    isSessionExpired: jest.fn(),
  },
}));

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}));

// Now import the hooks
import { AuthProvider, useAuth } from '../useAuth';
import { AuthClient } from '../../api';

// Test component that uses the auth context
const TestComponent = () => {
  const { authState, login, logout, register } = useAuth();
  
  return (
    <div>
      <div data-testid="auth-state">
        {JSON.stringify(authState)}
      </div>
      <button 
        data-testid="login-button" 
        onClick={() => login({ email: 'test@example.com', password: 'password' })}
      >
        Login
      </button>
      <button 
        data-testid="register-button" 
        onClick={() => register({ email: 'test@example.com', password: 'password', name: 'Test User' })}
      >
        Register
      </button>
      <button 
        data-testid="logout-button" 
        onClick={() => logout()}
      >
        Logout
      </button>
    </div>
  );
};

describe('useAuth', () => {
  const pushMock = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    
    // Setup router mock
    (useRouter as jest.Mock).mockReturnValue({
      push: pushMock,
      replace: jest.fn(),
    });
    
    // Default mocks for AuthClient
    (AuthClient.isSessionExpired as jest.Mock).mockReturnValue(true);
    (AuthClient.getCurrentUser as jest.Mock).mockResolvedValue(null);
  });
  
  it('should provide initial auth state', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    // Wait for initial auth check to complete
    await waitFor(() => {
      const authStateEl = screen.getByTestId('auth-state');
      expect(authStateEl.textContent).toContain('"isLoading":false');
      expect(authStateEl.textContent).toContain('"isAuthenticated":false');
    });
  });
  
  it('should handle login successfully', async () => {
    // Mock successful login and user data
    const tokenData = { 
      access_token: 'test-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer'
    };
    const userData = { 
      id: 1, 
      email: 'test@example.com',
      name: 'Test User',
      is_active: true
    };
    
    (AuthClient.login as jest.Mock).mockResolvedValue(tokenData);
    (AuthClient.getCurrentUser as jest.Mock).mockResolvedValue(userData);
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    // Click login button
    const loginButton = screen.getByTestId('login-button');
    await act(async () => {
      loginButton.click();
    });
    
    // Wait for login process to complete
    await waitFor(() => {
      // Check that token was stored
      expect(AuthClient.storeTokens).toHaveBeenCalledWith(tokenData);
      
      // Check that user data was fetched
      expect(AuthClient.getCurrentUser).toHaveBeenCalled();
    });

    // Check that auth state was updated
    const authStateEl = screen.getByTestId('auth-state');
    expect(authStateEl.textContent).toContain('"isAuthenticated":true');
    
    // Check for redirect to dashboard
    expect(pushMock).toHaveBeenCalledWith('/dashboard');
  });
  
  it('should handle login failure', async () => {
    // Mock failed login
    (AuthClient.login as jest.Mock).mockRejectedValue(new Error('Invalid credentials'));
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    // Click login button
    const loginButton = screen.getByTestId('login-button');
    await act(async () => {
      loginButton.click();
    });
    
    // Wait for login process to complete
    await waitFor(() => {
      // Check that auth state contains error
      const authStateEl = screen.getByTestId('auth-state');
      expect(authStateEl.textContent).toContain('"isAuthenticated":false');
      
      // Check that we did not redirect
      expect(pushMock).not.toHaveBeenCalled();
    });
  });
  
  it('should handle successful registration', async () => {
    // Mock successful registration and login
    const userData = { 
      id: 1, 
      email: 'test@example.com', 
      name: 'Test User',
      is_active: true
    };
    const tokenData = { 
      access_token: 'test-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer'
    };
    
    (AuthClient.register as jest.Mock).mockResolvedValue(userData);
    (AuthClient.login as jest.Mock).mockResolvedValue(tokenData);
    (AuthClient.getCurrentUser as jest.Mock).mockResolvedValue(userData);
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    // Click register button
    const registerButton = screen.getByTestId('register-button');
    await act(async () => {
      registerButton.click();
    });
    
    // Wait for registration and login to complete
    await waitFor(() => {
      // Check that register was called
      expect(AuthClient.register).toHaveBeenCalled();
      
      // Check that login was called after registration
      expect(AuthClient.login).toHaveBeenCalled();
    });
  });
  
  it('should handle logout correctly', async () => {
    // Setup authenticated state first
    const userData = { 
      id: 1, 
      email: 'test@example.com', 
      name: 'Test User',
      is_active: true
    };
    
    // Mock initial authenticated state
    (AuthClient.isSessionExpired as jest.Mock).mockReturnValue(false);
    (AuthClient.getCurrentUser as jest.Mock).mockResolvedValue(userData);
    localStorage.setItem('access_token', 'test-token');
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    // Wait for initial auth check to complete and show authenticated state
    await waitFor(() => {
      const authStateEl = screen.getByTestId('auth-state');
      expect(authStateEl.textContent).toContain('"isAuthenticated":true');
    });
    
    // Click logout button
    const logoutButton = screen.getByTestId('logout-button');
    await act(async () => {
      logoutButton.click();
    });
    
    // Wait for logout to complete
    await waitFor(() => {
      // Check that logout was called
      expect(AuthClient.logout).toHaveBeenCalled();
    });
  });
});