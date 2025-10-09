/**
 * @fileoverview Jest configuration for comprehensive testing
 * Includes coverage thresholds, test environment, and performance settings
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',

  // Setup files to run before tests
  setupFilesAfterEnv: [
    '<rootDir>/src/setupTests.js'
  ],

  // Test file patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/?(*.)(test|spec).{js,jsx,ts,tsx}'
  ],

  // Module name mapping for path aliases
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@atoms/(.*)$': '<rootDir>/src/components/atoms/$1',
    '^@molecules/(.*)$': '<rootDir>/src/components/molecules/$1',
    '^@organisms/(.*)$': '<rootDir>/src/components/organisms/$1',
    '^@pages/(.*)$': '<rootDir>/src/components/pages/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@types/(.*)$': '<rootDir>/src/types/$1'
  },

  // Transform files
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
    '^.+\\.(css|scss|sass|less)$': 'jest-transform-css',
    '^.+\\.(svg|png|jpg|jpeg|gif|webp)$': '<rootDir>/src/__mocks__/fileMock.js'
  },

  // Transform ignore patterns
  transformIgnorePatterns: [
    'node_modules/(?!(@storybook/.*\\.js$|storybook/.*\\.js$))'
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/index.js',
    '!src/reportWebVitals.js',
    '!src/setupTests.js',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/__mocks__/**',
    '!src/mocks/**'
  ],

  // Coverage thresholds - strict requirements for production readiness
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    // Component-specific thresholds
    './src/components/': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    // Hook-specific thresholds
    './src/hooks/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    // Service-specific thresholds
    './src/services/': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    // Utility-specific thresholds
    './src/utils/': {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95
    }
  },

  // Coverage reporters
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json-summary',
    'cobertura'
  ],

  // Coverage output directory
  coverageDirectory: '<rootDir>/coverage',

  // Performance and timing
  testTimeout: 10000,

  // Slow test threshold
  slowTestThreshold: 5,

  // Bail out after first test failure in CI
  bail: process.env.CI ? 1 : 0,

  // Verbose output
  verbose: true,

  // Error handling
  errorOnDeprecated: true,

  // Cache configuration
  cache: true,
  cacheDirectory: '<rootDir>/node_modules/.cache/jest',

  // Watch mode configuration
  watchPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/coverage/',
    '<rootDir>/build/'
  ],

  // Test results processing
  testResultsProcessor: 'jest-sonar-reporter',

  // Global setup and teardown
  globalSetup: '<rootDir>/src/__tests__/setup/globalSetup.js',
  globalTeardown: '<rootDir>/src/__tests__/setup/globalTeardown.js',

  // Reporter configuration
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: '<rootDir>/test-results',
      outputName: 'junit.xml',
      classNameTemplate: '{classname}',
      titleTemplate: '{title}',
      ancestorSeparator: ' › ',
      usePathForSuiteName: true
    }],
    ['jest-html-reporter', {
      pageTitle: 'namaskah Frontend Test Report',
      outputPath: '<rootDir>/test-results/test-report.html'
    }]
  ],

  // Snapshot configuration
  snapshotSerializers: [
    'enzyme-to-json/serializer'
  ],

  // Module directories
  moduleDirectories: [
    'node_modules',
    '<rootDir>/src'
  ],

  // Test environment options
  testEnvironmentOptions: {
    url: 'http://localhost:3000'
  },

  // Clear mocks between tests
  clearMocks: true,

  // Reset modules between tests
  resetModules: true,

  // Restore mocks between tests
  restoreMocks: true,

  // Maximum number of workers
  maxWorkers: '50%',

  // Detect memory leaks
  detectLeaks: true,

  // Force exit after tests
  forceExit: true,

  // Additional configuration for accessibility testing
  globals: {
    'jest-axe': {
      config: {
        rules: {
          // Disable overly strict rules for testing
          'color-contrast': { enabled: false },
          'link-in-text-block': { enabled: false }
        }
      }
    }
  },

  // Projects for different test types
  projects: [
    {
      displayName: 'unit',
      testMatch: ['**/__tests__/**/*.test.{js,jsx,ts,tsx}', '**/*.{test,spec}.{js,jsx,ts,tsx}'],
      testPathIgnorePatterns: ['integration', 'e2e']
    },
    {
      displayName: 'integration',
      testMatch: ['**/__tests__/**/integration/*.{js,jsx,ts,tsx}', '**/integration/**/*.{js,jsx,ts,tsx}'],
      setupFilesAfterEnv: ['<rootDir>/src/setupTests.js', '<rootDir>/src/__tests__/setup/integrationSetup.js']
    }
  ],

};