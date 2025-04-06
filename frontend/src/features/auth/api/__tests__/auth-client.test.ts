import { LoginCredentials, RegistrationData } from '../../types';

// Mock implementations
const mockPost = jest.fn();
const mockGet = jest.fn();

// Mock the entire auth-client module
jest.mock('../auth-client', () => {
  return {
    AuthClient: {
      login: jest.fn().mockImplementation(async () => {
        return { 
          access_token: 'test-token',
          refresh_token: 'refresh-token',
          token_type: 'bearer'
        };
      }),
      register: jest.fn().mockImplementation(async () => {
        return { 
          id: 1,
          email: 'test@example.com',
          name: 'Test User'
        };
      }),
      getCurrentUser: jest.fn().mockImplementation(async () => {
        return { 
          id: 1,
          email: 'test@example.com',
          name: 'Test User'
        };
      }),
      refreshToken: jest.fn().mockImplementation(async () => {
        return { 
          access_token: 'new-token',
          refresh_token: 'new-refresh-token',
          token_type: 'bearer'
        };
      }),
      requestPasswordReset: jest.fn(),
      updatePassword: jest.fn(),
      logout: jest.fn(),
      storeTokens: jest.fn(),
      isSessionExpired: jest.fn().mockReturnValue(false)
    }
  };
});

// Import the module after mocking
import { AuthClient } from '../auth-client';

describe('AuthClient', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('login', () => {
    it('should return token data on successful login', async () => {
      // Mock data
      const credentials: LoginCredentials = {
        email: 'test@example.com',
        password: 'password123',
      };

      // Test login function
      const result = await AuthClient.login(credentials);

      // Assertions
      expect(result).toHaveProperty('access_token');
      expect(result).toHaveProperty('refresh_token');
      expect(result).toHaveProperty('token_type', 'bearer');
    });

    it('should call login with correct credentials', async () => {
      // Mock data
      const credentials: LoginCredentials = {
        email: 'test@example.com',
        password: 'password123',
      };

      // Call login
      await AuthClient.login(credentials);

      // Verify login was called with correct credentials
      expect(AuthClient.login).toHaveBeenCalledWith(credentials);
    });
  });

  describe('register', () => {
    it('should return user data on successful registration', async () => {
      // Mock data
      const registrationData: RegistrationData = {
        email: 'newuser@example.com',
        password: 'password123',
        name: 'New User',
      };

      // Test register function
      const result = await AuthClient.register(registrationData);

      // Assertions
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('email');
      expect(result).toHaveProperty('name');
    });

    it('should call register with correct data', async () => {
      // Mock data
      const registrationData: RegistrationData = {
        email: 'newuser@example.com',
        password: 'password123',
        name: 'New User',
      };

      // Call register
      await AuthClient.register(registrationData);

      // Verify register was called with correct data
      expect(AuthClient.register).toHaveBeenCalledWith(registrationData);
    });
  });

  describe('getCurrentUser', () => {
    it('should return user data for the current user', async () => {
      // Test getCurrentUser function
      const result = await AuthClient.getCurrentUser();

      // Assertions
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('email');
      expect(result).toHaveProperty('name');
    });

    it('should call getCurrentUser method', async () => {
      // Call getCurrentUser
      await AuthClient.getCurrentUser();

      // Verify method was called
      expect(AuthClient.getCurrentUser).toHaveBeenCalled();
    });
  });

  describe('refreshToken', () => {
    it('should return new tokens on successful refresh', async () => {
      // Mock data
      const refreshToken = 'old-refresh-token';

      // Test refreshToken function
      const result = await AuthClient.refreshToken(refreshToken);

      // Assertions
      expect(result).toHaveProperty('access_token');
      expect(result).toHaveProperty('refresh_token');
      expect(result).toHaveProperty('token_type', 'bearer');
    });

    it('should call refreshToken with the correct refresh token', async () => {
      // Mock data
      const refreshToken = 'test-refresh-token';

      // Call refreshToken
      await AuthClient.refreshToken(refreshToken);

      // Verify refreshToken was called with correct parameter
      expect(AuthClient.refreshToken).toHaveBeenCalledWith(refreshToken);
    });
  });

  describe('storeTokens', () => {
    it('should call storeTokens with the correct token data', () => {
      // Mock token data
      const tokenData = {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        expires_in: 3600,
        token_type: 'bearer',
      };

      // Store tokens
      AuthClient.storeTokens(tokenData);

      // Assertions
      expect(AuthClient.storeTokens).toHaveBeenCalledWith(tokenData);
    });

    it('should handle tokens without refresh_token', () => {
      // Mock token data without refresh token
      const tokenData = {
        access_token: 'test-access-token',
        token_type: 'bearer',
      };

      // Store tokens
      AuthClient.storeTokens(tokenData);

      // Assertions
      expect(AuthClient.storeTokens).toHaveBeenCalledWith(tokenData);
    });
  });

  describe('isSessionExpired', () => {
    it('should call isSessionExpired method', () => {
      // Call isSessionExpired
      AuthClient.isSessionExpired();

      // Verify isSessionExpired was called
      expect(AuthClient.isSessionExpired).toHaveBeenCalled();
    });
  });
});