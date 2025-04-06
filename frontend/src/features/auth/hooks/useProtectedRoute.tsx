import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from './useAuth';

/**
 * Hook to protect routes that require authentication
 * @param {string} redirectPath - Path to redirect if not authenticated (default: /auth/login)
 */
export const useProtectedRoute = (redirectPath: string = '/auth/login') => {
  const { authState } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If not loading and not authenticated, redirect
    if (!authState.isLoading && !authState.isAuthenticated) {
      router.push(redirectPath);
    }
  }, [authState.isLoading, authState.isAuthenticated, router, redirectPath]);

  return {
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    user: authState.user,
  };
};
