import React from 'react';
import { ProtectedRoute } from '../../features/auth/components';
import { AuthProvider } from '../../features/auth/hooks';

const DashboardPage: React.FC = () => {
  return (
    <AuthProvider>
      <ProtectedRoute>
        <div className="dashboard-page">
          <h1>Dashboard</h1>
          <p>Welcome to your dashboard!</p>
        </div>
      </ProtectedRoute>
    </AuthProvider>
  );
};

export default DashboardPage;
