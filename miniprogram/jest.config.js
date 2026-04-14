/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'node',
  roots: ['<rootDir>/__tests__'],
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],
  moduleNameMapper: {
    '^../../utils/api$': '<rootDir>/utils/api.js',
    '^../../utils/config$': '<rootDir>/utils/config.js',
  },
  testMatch: ['**/*.test.js'],
};
