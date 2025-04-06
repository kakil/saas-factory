import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useAuth } from '../hooks';
import { LoginCredentials } from '../types';
import Link from 'next/link';

export const LoginForm: React.FC = () => {
  const { authState, login } = useAuth();
  const { register, handleSubmit, formState: { errors } } = useForm<LoginCredentials>();

  const onSubmit = async (data: LoginCredentials) => {
    await login(data);
  };

  return (
    <div className="auth-form">
      <h2>Log In</h2>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            {...register('email', { 
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address',
              } 
            })}
          />
          {errors.email && <span className="error">{errors.email.message}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            {...register('password', { 
              required: 'Password is required',
              minLength: {
                value: 8,
                message: 'Password must be at least 8 characters'
              } 
            })}
          />
          {errors.password && <span className="error">{errors.password.message}</span>}
        </div>

        {authState.error && <div className="error-message">{authState.error}</div>}

        <div className="form-actions">
          <button type="submit" disabled={authState.isLoading}>
            {authState.isLoading ? 'Loading...' : 'Log In'}
          </button>
        </div>

        <div className="auth-links">
          <p>
            Don't have an account? <Link href="/auth/register">Register</Link>
          </p>
          <p>
            <Link href="/auth/forgot-password">Forgot password?</Link>
          </p>
        </div>
      </form>
    </div>
  );
};
