import React from 'react';
import { RegisterForm } from '../../features/auth/components';
import { AuthProvider } from '../../features/auth/hooks';

const RegisterPage: React.FC = () => {
  return (
    <AuthProvider>
      <div className="auth-page">
        <div className="auth-container">
          <RegisterForm />
        </div>
      </div>
    </AuthProvider>
  );
};

export default RegisterPage;
