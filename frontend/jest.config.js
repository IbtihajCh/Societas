const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  testEnvironment: 'jest-environment-jsdom',
  moduleDirectories: ['node_modules', '<rootDir>/'],
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/.next/'],
  coverageReporters: ['text', 'lcov'],
  collectCoverageFrom: [
    'src/components/**/*.{ts,tsx}',
    'src/contexts/**/*.{ts,tsx}',
    'src/services/**/*.{ts,tsx}',
    'src/hooks/**/*.{ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      lines: 0,
    },
  },
};

module.exports = createJestConfig(customJestConfig);
