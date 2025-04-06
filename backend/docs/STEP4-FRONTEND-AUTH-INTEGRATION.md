# SaaS Factory - Frontend Auth Integration

This document provides an overview of the Frontend Authentication Integration implemented in Step 4 of the SaaS Factory Blueprint application.

## Overview

The Frontend Authentication Integration focuses on creating a seamless authentication experience that works with the backend's dual authentication system (JWT and Supabase). It covers these key areas:

1. **Authentication Strategy** - Supporting both JWT and Supabase authentication flows
2. **Frontend Authentication Components** - Reusable UI components for auth operations
3. **Integration Testing** - End-to-end testing of the authentication system

## Architecture

The frontend authentication system uses a clean, layered architecture:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   UI        │ --> │   Hooks     │ --> │   API       │
│  Components │     │  (Context)  │     │  Client     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Routes    │     │   Storage   │     │ Token Mgmt  │
└─────────────┘     └─────────────┘     └─────────────┘
```

- **UI Components**: Login/register forms and protected route wrappers
- **Hooks/Context**: React context for global auth state management
- **API Client**: Communication with backend auth endpoints
- **Routes**: Authentication-aware routing system
- **Storage**: Secure token storage mechanisms
- **Token Management**: Access and refresh token handling

## Key Components

### 1. Authentication Strategy

The frontend authentication system is designed to work with multiple backend auth providers through a unified interface:

- Support for both JWT-based auth and Supabase Auth
- Flexible provider system for adding new auth methods
- Seamless migration path between providers

#### Authentication Flow:

1. User enters credentials in the login form
2. Credentials are sent to the backend auth endpoint
3. Backend validates credentials and returns tokens
4. Frontend stores tokens and user information
5. Protected routes use tokens for subsequent API calls
6. Token refresh is handled automatically when needed

#### Migration Strategy:

The system allows for a gradual migration from JWT to Supabase:

```typescript
// AuthClient provides a unified interface for both JWT and Supabase auth
export const AuthClient = {
  // Common login method that works with both providers
  async login(credentials: LoginCredentials): Promise<Token> {
    try {
      // Try JWT auth first
      const response = await apiClient.post<Token>('/auth/login', credentials);
      return response.data;
    } catch (error) {
      // Fallback to Supabase auth if needed
      if (useSupabaseAuth) {
        return await supabaseLogin(credentials);
      }
      throw new Error('Authentication failed');
    }
  },

  // Other auth methods follow the same pattern...
};
```

### 2. Frontend Authentication Components

The system includes a complete set of authentication UI components:

- Login form
- Registration form
- Password reset
- Protected route wrapper
- User profile management

#### Auth Context Provider:

```tsx
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // Check authentication status on mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        // Check if we have tokens
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

        // Refresh token if needed
        if (isTokenExpired(token)) {
          await refreshToken();
        }

        // Get user profile
        const user = await AuthClient.getCurrentUser();
        setAuthState({
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        // Handle error and logout
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: 'Authentication failed',
        });
        await logout();
      }
    };

    checkAuthStatus();
  }, []);

  // Auth methods (login, register, logout, etc.)
  const login = async (credentials: LoginCredentials) => {/* ... */};
  const register = async (data: RegistrationData) => {/* ... */};
  const logout = async () => {/* ... */};
  const refreshToken = async () => {/* ... */};

  return (
    <AuthContext.Provider
      value={{
        authState,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
```

#### Protected Route Component:

```tsx
export const ProtectedRoute: React.FC<{ 
  children: ReactNode, 
  redirectTo?: string 
}> = ({ 
  children, 
  redirectTo = '/auth/login' 
}) => {
  const { authState } = useAuth();
  const router = useRouter();

  // Show loading state
  if (authState.isLoading) {
    return <LoadingSpinner />;
  }

  // Redirect to login if not authenticated
  if (!authState.isAuthenticated) {
    if (typeof window !== 'undefined') {
      router.replace(redirectTo);
    }
    return null;
  }

  // Render children if authenticated
  return <>{children}</>;
};
```

### 3. Integration Testing

The authentication system includes comprehensive testing for all components:

- Unit tests for auth hooks and context
- Component tests for auth forms
- Integration tests for the complete auth flow
- End-to-end tests with mocked backend

#### Testing Strategy:

```tsx
// Example test for login functionality
describe('Login Functionality', () => {
  it('should authenticate a user with valid credentials', async () => {
    // Setup mocked API responses
    mockApiClient.onPost('/auth/login').reply(200, {
      access_token: 'test-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer'
    });
    
    mockApiClient.onGet('/users/me').reply(200, {
      id: 1,
      email: 'test@example.com',
      name: 'Test User'
    });

    // Render login form
    const { getByLabelText, getByText } = render(
      <AuthProvider>
        <LoginForm />
      </AuthProvider>
    );

    // Fill in credentials
    fireEvent.change(getByLabelText(/email/i), {
      target: { value: 'test@example.com' }
    });
    
    fireEvent.change(getByLabelText(/password/i), {
      target: { value: 'password123' }
    });

    // Submit form
    fireEvent.click(getByText(/log in/i));

    // Wait for auth state to update
    await waitFor(() => {
      expect(localStorage.getItem('access_token')).toBe('test-token');
    });
  });
});
```

## Implementation Details

### 1. Types and Interfaces

```typescript
// Authentication state
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// User model
export interface User {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  supabase_uid?: string;
}

// Authentication tokens
export interface Token {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
  token_type: string;
}

// Login credentials
export interface LoginCredentials {
  email: string;
  password: string;
}

// Registration data
export interface RegistrationData {
  email: string;
  password: string;
  name: string;
  organization_name?: string;
}
```

### 2. API Client

```typescript
// Auth API client
export const AuthClient = {
  // Login with credentials
  async login(credentials: LoginCredentials): Promise<Token> {
    const response = await apiClient.post<Token>('/auth/login', credentials);
    return response.data;
  },

  // Register a new user
  async register(data: RegistrationData): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', data);
    return response.data;
  },

  // Get current user profile
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/users/me');
    return response.data;
  },

  // Request password reset
  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post('/auth/reset-password', { email });
  },

  // Refresh access token
  async refreshToken(refreshToken: string): Promise<Token> {
    const response = await apiClient.post<Token>('/auth/refresh', {
      refresh_token: refreshToken
    });
    return response.data;
  }
};
```

### 3. Token Management

```typescript
// Store authentication tokens
export const storeTokens = (token: Token): void => {
  localStorage.setItem('access_token', token.access_token);
  
  if (token.refresh_token) {
    localStorage.setItem('refresh_token', token.refresh_token);
  }
  
  if (token.expires_in) {
    const expiresAt = Date.now() + token.expires_in * 1000;
    localStorage.setItem('expires_at', expiresAt.toString());
  }
};

// Check if token is expired
export const isTokenExpired = (): boolean => {
  const expiresAt = localStorage.getItem('expires_at');
  if (!expiresAt) return true;
  
  return Date.now() > parseInt(expiresAt);
};

// Clear all auth tokens
export const clearTokens = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('expires_at');
};
```

## Pages and Routing

The authentication system includes these main pages:

### Login Page

```tsx
const LoginPage: React.FC = () => {
  return (
    <AuthLayout title="Login">
      <LoginForm />
      <LinkContainer>
        <Link href="/auth/register">Don't have an account? Register</Link>
        <Link href="/auth/forgot-password">Forgot password?</Link>
      </LinkContainer>
    </AuthLayout>
  );
};
```

### Registration Page

```tsx
const RegisterPage: React.FC = () => {
  return (
    <AuthLayout title="Create an Account">
      <RegisterForm />
      <LinkContainer>
        <Link href="/auth/login">Already have an account? Login</Link>
      </LinkContainer>
    </AuthLayout>
  );
};
```

### Protected Dashboard

```tsx
const DashboardPage: React.FC = () => {
  // Get auth state
  const { authState } = useAuth();

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <h1>Welcome, {authState.user?.name}!</h1>
        <DashboardContent />
      </DashboardLayout>
    </ProtectedRoute>
  );
};
```

## Setup and Configuration

The frontend authentication system requires these environment variables:

```
# API URL for backend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase configuration
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-public-key

# Auth configuration
NEXT_PUBLIC_AUTH_PROVIDER=jwt  # or 'supabase'
```

## Integration with Backend

The frontend auth system integrates with the backend's dual authentication system:

1. **JWT Authentication**:
   - Backend validates JWT tokens using the secret key
   - Frontend stores and manages JWT tokens
   - Token refresh is handled by the backend `/auth/refresh` endpoint

2. **Supabase Authentication**:
   - Backend validates Supabase tokens with Supabase Auth
   - Frontend uses Supabase client for auth operations
   - User mapping between Supabase and application database

## Migration Path

The migration path from JWT to Supabase Auth follows these steps:

1. **Initial State (JWT only)**:
   - Frontend uses JWT auth exclusively
   - Tokens managed by the application

2. **Parallel Implementation**:
   - Backend supports both JWT and Supabase tokens
   - Frontend adds Supabase client but still defaults to JWT
   - Feature flag controls which auth method is used

3. **Gradual Migration**:
   - New users are created with Supabase Auth
   - Existing users continue with JWT tokens
   - Backend handles both auth methods transparently

4. **Complete Migration**:
   - All users migrated to Supabase Auth
   - JWT auth is deprecated but still supported
   - Frontend defaults to Supabase Auth

## Security Considerations

Important security considerations for the authentication system:

1. **Token Storage**:
   - Tokens are stored in localStorage for simplicity
   - For production, consider more secure storage options
   - Implement token encryption for enhanced security

2. **CSRF Protection**:
   - All state-changing requests require proper CSRF tokens
   - Implement CSRF protection in the API client

3. **XSS Protection**:
   - Sanitize all user inputs to prevent XSS attacks
   - Use Content Security Policy headers

4. **Session Management**:
   - Implement automatic session timeout
   - Allow users to manage active sessions
   - Provide logout functionality across devices

## Testing

Run authentication tests with:

```bash
# Run component tests
npm test

# Run integration tests
npm run test:integration

# Run end-to-end tests
npm run test:e2e
```

## Common Operations

### User Login

```typescript
// In a component
const { login } = useAuth();

// Handle form submission
const handleSubmit = async (data: LoginCredentials) => {
  try {
    await login(data);
    // Redirect to dashboard on success
    router.push('/dashboard');
  } catch (error) {
    // Handle error
    setError('Invalid credentials');
  }
};
```

### Registration

```typescript
// In a component
const { register } = useAuth();

// Handle form submission
const handleSubmit = async (data: RegistrationData) => {
  try {
    await register(data);
    // User is automatically logged in after registration
    router.push('/dashboard');
  } catch (error) {
    // Handle error
    setError('Registration failed');
  }
};
```

### Access Protected Resources

```typescript
// In a component
const { authState } = useAuth();

// Make authenticated API call
const fetchData = async () => {
  try {
    // API client automatically includes auth token
    const response = await apiClient.get('/protected-resource');
    setData(response.data);
  } catch (error) {
    // Handle error (including auth errors)
    if (error.response?.status === 401) {
      // Handle unauthorized error
    }
  }
};
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check that credentials are correct
   - Verify that the backend auth service is running
   - Check for CORS issues in the browser console

2. **Token Refresh Issues**
   - Ensure refresh token is stored correctly
   - Check backend logs for token validation errors
   - Verify that token refresh endpoint is working

3. **Protected Route Flashes**
   - Implement a loading state for auth status checks
   - Use server-side authentication for critical routes
   - Consider static generation for public pages

## Resources

- [NextJS Authentication Documentation](https://nextjs.org/docs/authentication)
- [Supabase Auth Documentation](https://supabase.io/docs/guides/auth)
- [Web Authentication Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT.io](https://jwt.io/) - JWT debugging and validation