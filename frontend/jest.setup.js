// Import the required testing library
require('@testing-library/jest-dom');

// Mock the localStorage API
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

// Define localStorage globally for tests
global.localStorage = localStorageMock;

// Mock Next.js router - but leave the actual mocking to individual test files
jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}));

// Reset mocks between tests
beforeEach(() => {
  jest.clearAllMocks();
  localStorageMock.clear();
});