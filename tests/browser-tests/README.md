# Browser Extension UI Tests

This directory contains automated tests for the AI-powered Tax Law Assistant browser extension. These tests validate the UI functionality, memo storage capabilities, and API interactions of the extension.

## Test Suite Overview

The test suite is divided into three main files:

1. **ui_test.js** - Tests for the extension's popup interface and inline suggestions
2. **memo_storage_test.js** - Tests for creating, storing, and retrieving quick memos
3. **api_response_test.js** - Tests for API calls, response handling, and citation formatting

## Setup Requirements

To run these tests, you'll need:

- Node.js (v14 or higher)
- Chrome browser
- The browser extension built in the `/browser-extension/dist` directory

## Installation

1. Navigate to the test directory:
   ```
   cd /Users/andreibeniash/Desktop/taxai/tests/browser-tests
   ```

2. Install dependencies:
   ```
   npm install
   ```

## Running Tests

To run all tests:
```
npm test
```

To run a specific test file:
```
npx jest ui_test.js
npx jest memo_storage_test.js
npx jest api_response_test.js
```

## Test Configuration

Tests use Jest and Puppeteer to automate browser interactions. The configuration is in:
- `jest-puppeteer.config.js` - Controls browser launch options
- `package.json` - Contains Jest configuration

## Important Notes

- Tests require the extension to be built in the `/browser-extension/dist` directory
- Tests run in a non-headless browser to properly load Chrome extensions
- Some tests may be skipped if certain features are not yet implemented in the extension

## Troubleshooting

If tests fail:
1. Ensure the extension is properly built in the dist directory
2. Check CSS selectors in test files match those in the actual extension
3. Adjust timeouts if necessary for slower operations

## Adding New Tests

To add new tests:
1. Add test functions to the appropriate test file
2. Follow the existing pattern of `describe` and `test` blocks
3. Use Puppeteer's page interaction methods to test UI functionality

## CI/CD Integration

These tests can be integrated into a CI/CD pipeline by:
1. Building the extension first
2. Running tests in a headless environment (with special Chrome flags)
3. Using a tool like xvfb for headless environments that require a display