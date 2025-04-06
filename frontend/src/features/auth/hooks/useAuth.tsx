import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/router';
import { AuthClient } from '../api';
import { AuthState, User, LoginCredentials, RegistrationData, Token } from '../types';

// Initial auth state
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Create the auth context
const AuthContext = createContext<{
  authState: AuthState;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegistrationData) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}>({ 
  authState: initialState,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
  refreshAuth: async () => {},
});

// Auth provider props
interface AuthProviderProps {
  children: ReactNode;
}

// Authentication provider component
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [authState, setAuthState] = useState<AuthState>(initialState);
  const router = useRouter();

  // Check if user is already authenticated on mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        setAuthState((prev) => ({ ...prev, isLoading: true }));

        // Check if we have tokens in storage
        const token = localStorage.getItem('access_token');
        if (!token) {
          setAuthState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
          return;
        }

        // Check if token is expired and try to refresh if needed
        if (AuthClient.isSessionExpired()) {
          const refreshToken = localStorage.getItem('refresh_token');
          if (!refreshToken) {
            await logout();
            return;
          }

          try {
            // Try to refresh the token
            const newToken = await AuthClient.refreshToken(refreshToken);
            AuthClient.storeTokens(newToken);
          } catch (error) {
            await logout();
            return;
          }
        }

        // Get user data with the token
        const user = await AuthClient.getCurrentUser();
        setAuthState({
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        await logout();
      }
    };

    checkAuthStatus();
  }, []);

  // Login function
  const login = async (credentials: LoginCredentials) => {
    try {
      setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));

      // Authenticate with the API
      const token = await AuthClient.login(credentials);
      
      // Store tokens
      AuthClient.storeTokens(token);

      // Get user profile
      const user = await AuthClient.getCurrentUser();

      // Update state
      setAuthState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (error) {
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'Invalid credentials',
      });
    }
  };

  // Register function
  const register = async (data: RegistrationData) => {
    try {
      setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));

      // Register user
      await AuthClient.register(data);

      // Login with the new credentials
      await login({
        email: data.email,
        password: data.password,
      });
    } catch (error) {
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'Registration failed',
      });
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await AuthClient.logout();
      
      // Clear state
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });

      // Redirect to login
      router.push('/auth/login');
    } catch (error) {
      setAuthState((prev) => ({ 
        ...prev, 
        error: 'Logout failed',
      }));
    }
  };

  // Refresh authentication state
  const refreshAuth = async () => {
    try {
      setAuthState((prev) => ({ ...prev, isLoading: true }));

      // Get user data with the token
      const user = await AuthClient.getCurrentUser();
      setAuthState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      // If we can't get user data, log out
      await logout();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        authState,
        login,
        register,
        logout,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
