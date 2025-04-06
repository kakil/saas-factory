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

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegistrationData {
  email: string;
  password: string;
  name: string;
  organization_name?: string;
  is_superuser?: boolean;
}

export interface ResetPasswordData {
  email: string;
}

export interface UpdatePasswordData {
  token: string;
  new_password: string;
}

export interface Token {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export enum AuthProvider {
  JWT = 'jwt',
  SUPABASE = 'supabase'
}
