import React from 'react';
import { useForm } from 'react-hook-form';
import { useAuth } from '../hooks';
import { RegistrationData } from '../types';
import Link from 'next/link';

export const RegisterForm: React.FC = () => {
  const { authState, register: registerUser } = useAuth();
  const { register, handleSubmit, formState: { errors }, watch } = useForm<RegistrationData & { confirmPassword: string }>();
  const password = watch('password', '');

  const onSubmit = async (data: RegistrationData & { confirmPassword: string }) => {
    const { confirmPassword, ...registrationData } = data;
    await registerUser(registrationData);
  };

  return (
    <div className="auth-form">
      <h2>Create an Account</h2>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="form-group">
          <label htmlFor="name">Full Name</label>
          <input
            id="name"
            type="text"
            {...register('name', { required: 'Full name is required' })}
          />
          {errors.name && <span className="error">{errors.name.message}</span>}
        </div>

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
          <label htmlFor="organization_name">Organization Name (Optional)</label>
          <input
            id="organization_name"
            type="text"
            {...register('organization_name')}
          />
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

        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            type="password"
            {...register('confirmPassword', { 
              required: 'Please confirm your password',
              validate: value => value === password || 'Passwords do not match'
            })}
          />
          {errors.confirmPassword && <span className="error">{errors.confirmPassword.message}</span>}
        </div>

        {authState.error && <div className="error-message">{authState.error}</div>}

        <div className="form-actions">
          <button type="submit" disabled={authState.isLoading}>
            {authState.isLoading ? 'Loading...' : 'Register'}
          </button>
        </div>

        <div className="auth-links">
          <p>
            Already have an account? <Link href="/auth/login">Log In</Link>
          </p>
        </div>
      </form>
    </div>
  );
};
