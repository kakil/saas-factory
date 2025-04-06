import React from 'react';
import { AppProps } from 'next/app';
import { AuthProvider } from '../features/auth/hooks';
import '../styles/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

export default MyApp;
