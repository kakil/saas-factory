import React from 'react';
import { LoginForm } from '../../features/auth/components';
import { AuthProvider } from '../../features/auth/hooks';

const LoginPage: React.FC = () => {
  return (
    <AuthProvider>
      <div className="auth-page">
        <div className="auth-container">
          <LoginForm />
        </div>
      </div>
    </AuthProvider>
  );
};

export default LoginPage;
