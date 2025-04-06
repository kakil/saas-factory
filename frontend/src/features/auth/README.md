# SaaS Factory Authentication System

This document describes the authentication system implemented for the SaaS Factory Blueprint application. The system supports both JWT and Supabase authentication methods, providing a flexible and secure approach to user authentication.

## Architecture Overview

The authentication system is built with a flexible architecture that allows for different authentication providers while maintaining a consistent API for the frontend.

### Key Components:

1. **AuthClient** - Core API client for authentication operations
2. **AuthContext/Provider** - React context for managing authentication state
3. **Authentication Forms** - UI components for login, registration, and password reset
4. **Protected Routes** - Components for restricting access to authenticated users
5. **Token Management** - Utilities for handling access and refresh tokens

## Authentication Flow

### 1. Login Flow:
- User enters credentials (email/password)
- Credentials are sent to the backend `/auth/login` endpoint
- On successful authentication, backend returns access and refresh tokens
- Tokens are stored in localStorage
- User is redirected to the dashboard

### 2. Registration Flow:
- User completes registration form
- Data is sent to the backend `/auth/register` endpoint
- On successful registration, user is automatically logged in
- User is redirected to the dashboard

### 3. Token Refresh Flow:
- When an access token expires, the refresh token is used to obtain a new access token
- If refresh fails, user is logged out and redirected to login

### 4. Protected Routes:
- Routes that require authentication check the current authentication state
- If user is not authenticated, they are redirected to the login page
- If authentication is in progress (loading), a loading indicator is shown

## Dual Authentication Support

The system is designed to work with both custom JWT tokens and Supabase authentication:

### JWT Authentication:
- Standard JWT tokens issued by the FastAPI backend
- Token validation and refresh handled by the backend

### Supabase Authentication:
- Integration with Supabase Auth service
- Uses Supabase client for auth operations
- Tokens compatible with both the backend and Supabase services

## File Structure

```
src/features/auth/
├── api/
│   ├── auth-client.ts   # API client for auth operations
│   └── index.ts
├── components/
│   ├── ForgotPasswordForm.tsx # Password reset form
│   ├── LoginForm.tsx          # Login form
│   ├── ProtectedRoute.tsx     # Route protection component
│   ├── RegisterForm.tsx       # Registration form
│   └── index.ts
├── hooks/
│   ├── index.ts
│   ├── useAuth.tsx            # Auth context and provider
│   └── useProtectedRoute.tsx  # Hook for route protection
├── types/
│   └── index.ts               # TypeScript interfaces
└── utils/
    └── index.ts               # Helper functions
```

## Usage Examples

### Protect a Route:

```tsx
import { ProtectedRoute } from 'features/auth/components';

const SecurePage = () => {
  return (
    <ProtectedRoute>
      <div>This content is only visible to authenticated users</div>
    </ProtectedRoute>
  );
};
```

### Access Auth State and Methods:

```tsx
import { useAuth } from 'features/auth/hooks';

const MyComponent = () => {
  const { authState, login, logout } = useAuth();
  
  if (authState.isLoading) {
    return <div>Loading...</div>;
  }
  
  return (
    <div>
      {authState.isAuthenticated ? (
        <>
          <p>Welcome, {authState.user?.name}</p>
          <button onClick={logout}>Logout</button>
        </>
      ) : (
        <button onClick={() => login({ email: 'test@example.com', password: 'password' })}>
          Login
        </button>
      )}
    </div>
  );
};
```

## Security Considerations

1. **Token Storage**: 
   - Tokens are stored in localStorage for simplicity
   - For production, consider using more secure options like HttpOnly cookies

2. **Token Refresh**: 
   - The system implements token refresh to maintain sessions
   - Refresh tokens are automatically used when access tokens expire

3. **Error Handling**:
   - Authentication errors are captured and displayed to users
   - Failed authentication attempts clear existing tokens

## Migration Path from JWT to Supabase

The system is designed to support a gradual migration from JWT to Supabase authentication:

1. **Dual Token Support**:
   - The backend validates both JWT and Supabase tokens
   - Frontend can work with either token type

2. **Provider Abstraction**:
   - Auth providers are abstracted behind a common interface
   - New providers can be added without changing the core API

3. **Migration Strategy**:
   - Start by adding Supabase client integration
   - Gradually migrate users to Supabase authentication
   - Eventually deprecate custom JWT authentication

## Configuration

The authentication system requires the following environment variables:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

## Future Improvements

1. **Social Authentication**: Add support for social login providers through Supabase
2. **Multi-factor Authentication**: Implement MFA for enhanced security
3. **Session Management**: Add the ability to view and manage active sessions
4. **Role-based Access Control**: Enhance route protection with role-based permissions