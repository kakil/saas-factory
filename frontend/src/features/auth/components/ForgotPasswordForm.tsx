import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { AuthClient } from '../api';
import { ResetPasswordData } from '../types';
import Link from 'next/link';

export const ForgotPasswordForm: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const { register, handleSubmit, formState: { errors } } = useForm<ResetPasswordData>();

  const onSubmit = async (data: ResetPasswordData) => {
    try {
      setIsLoading(true);
      setError(null);
      
      await AuthClient.requestPasswordReset(data);
      setSuccess(true);
    } catch (err) {
      setError('Failed to send password reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-form">
        <h2>Reset Link Sent</h2>
        <p>
          We've sent a password reset link to your email address. Please check your inbox and follow the instructions.
        </p>
        <div className="auth-links">
          <p>
            <Link href="/auth/login">Return to login</Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-form">
      <h2>Reset Your Password</h2>
      <p>Enter your email address and we'll send you a link to reset your password.</p>
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label htmlFor="email">Email Address</label>
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

        {error && <div className="error-message">{error}</div>}

        <div className="form-actions">
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </div>

        <div className="auth-links">
          <p>
            <Link href="/auth/login">Back to login</Link>
          </p>
        </div>
      </form>
    </div>
  );
};
