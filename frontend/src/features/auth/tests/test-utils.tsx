import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { AuthProvider } from '../hooks/useAuth';

// Custom render function that wraps the component with the AuthProvider
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => {
  return render(ui, { wrapper: AuthProvider, ...options });
};

// Re-export everything from testing-library
export * from '@testing-library/react';

// Override render method with our custom one
export { customRender as render };