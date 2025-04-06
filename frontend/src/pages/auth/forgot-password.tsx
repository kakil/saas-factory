import React from 'react';
import { ForgotPasswordForm } from '../../features/auth/components';
import { AuthProvider } from '../../features/auth/hooks';

const ForgotPasswordPage: React.FC = () => {
  return (
    <AuthProvider>
      <div className="auth-page">
        <div className="auth-container">
          <ForgotPasswordForm />
        </div>
      </div>
    </AuthProvider>
  );
};

export default ForgotPasswordPage;
