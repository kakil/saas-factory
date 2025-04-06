import React, { ReactNode } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../hooks/useAuth';

interface ProtectedRouteProps {
  children: ReactNode;
  redirectTo?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  redirectTo = '/auth/login',
}) => {
  const { authState } = useAuth();
  const router = useRouter();

  // If auth is being loaded, show a loading indicator
  if (authState.isLoading) {
    return <div className="auth-loading">Loading...</div>;
  }

  // If user is not authenticated, redirect to login
  if (!authState.isAuthenticated) {
    // Use router.replace instead of push to avoid adding to history
    router.replace(redirectTo);
    return null;
  }

  // If user is authenticated, render the protected content
  return <>{children}</>;
};
