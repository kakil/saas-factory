import axios from 'axios';
import { createClient } from '@supabase/supabase-js';
import {
  LoginCredentials,
  RegistrationData,
  ResetPasswordData,
  Token,
  UpdatePasswordData,
  User,
  RefreshTokenRequest,
} from '../types';

// Constants
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Axios client setup
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Supabase client setup
const supabaseClient = createClient(SUPABASE_URL, SUPABASE_KEY);

// Interceptor to add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Authentication service providing methods for auth operations
 */
export const AuthClient = {
  /**
   * Login with email and password using the FastAPI backend
   */
  async login(credentials: LoginCredentials): Promise<Token> {
    try {
      const response = await apiClient.post<Token>('/auth/login', credentials);
      return response.data;
    } catch (error) {
      throw new Error('Authentication failed');
    }
  },

  /**
   * Register a new user with the FastAPI backend
   */
  async register(data: RegistrationData): Promise<User> {
    try {
      const response = await apiClient.post<User>('/auth/register', data);
      return response.data;
    } catch (error) {
      throw new Error('Registration failed');
    }
  },

  /**
   * Get the current user profile
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await apiClient.get<User>('/users/me');
      return response.data;
    } catch (error) {
      throw new Error('Failed to get user profile');
    }
  },

  /**
   * Send a password reset request
   */
  async requestPasswordReset(data: ResetPasswordData): Promise<void> {
    try {
      await apiClient.post('/auth/reset-password', data);
    } catch (error) {
      throw new Error('Failed to send password reset request');
    }
  },

  /**
   * Update password using reset token
   */
  async updatePassword(data: UpdatePasswordData): Promise<void> {
    try {
      await apiClient.post('/auth/update-password', data);
    } catch (error) {
      throw new Error('Failed to update password');
    }
  },

  /**
   * Refresh the access token using a refresh token
   */
  async refreshToken(refreshToken: string): Promise<Token> {
    try {
      const payload: RefreshTokenRequest = { refresh_token: refreshToken };
      const response = await apiClient.post<Token>('/auth/refresh', payload);
      return response.data;
    } catch (error) {
      throw new Error('Failed to refresh token');
    }
  },

  /**
   * Logout from the application
   */
  async logout(): Promise<void> {
    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('expires_at');
  },

  /**
   * Store authentication tokens in local storage
   */
  storeTokens(token: Token): void {
    localStorage.setItem('access_token', token.access_token);
    
    if (token.refresh_token) {
      localStorage.setItem('refresh_token', token.refresh_token);
    }
    
    if (token.expires_in) {
      const expiresAt = Date.now() + token.expires_in * 1000;
      localStorage.setItem('expires_at', expiresAt.toString());
    }
  },

  /**
   * Check if the current session is expired
   */
  isSessionExpired(): boolean {
    const expiresAt = localStorage.getItem('expires_at');
    if (!expiresAt) return true;
    
    return Date.now() > parseInt(expiresAt);
  },
};
