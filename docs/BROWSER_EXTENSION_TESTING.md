# Testing the Browser Extension with OpenAI Integration

This document provides instructions for verifying that the browser extension can successfully communicate with the backend and receive responses from OpenAI.

## Prerequisites

1. Backend service is running and properly configured
2. Your OpenAI API key is set as an environment variable
3. The browser extension is loaded in your browser

## Starting the Backend

1. Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

2. Make the Maven wrapper executable:
   ```bash
   cd /Users/andreibeniash/Desktop/taxai/backend
   chmod +x mvnw
   ```

3. Start the backend service:
   ```bash
   ./mvnw spring-boot:run
   ```

4. Wait until you see a message indicating that the application has started.

## Loading the Browser Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" using the toggle in the top-right corner
3. Click "Load unpacked" and select the `/Users/andreibeniash/Desktop/taxai/browser-extension` directory
4. The Tax Law Assistant extension should now appear in your list of extensions

## Testing the Integration

### Method 1: Using the Extension Popup

1. Click on the Tax Law Assistant extension icon in your browser toolbar
2. In the popup, enter a tax-related question (e.g., "What is the standard deduction for 2024?")
3. Click "Search" or press Enter
4. You should see a response from OpenAI with information about your query

### Method 2: Using Context Menu on Tax Websites

1. Navigate to a tax-related website (e.g., irs.gov)
2. Select some text related to a tax topic
3. Right-click on the selected text
4. Choose "Ask Tax AI about this" from the context menu
5. A sidebar should appear with an AI response about the selected text

## Troubleshooting

If the browser extension isn't working correctly:

1. **Check the Console**:
   - Right-click on the extension popup and select "Inspect" to open Chrome DevTools
   - Look at the Console tab for any error messages

2. **Verify Backend Connectivity**:
   - Make sure the backend is running at http://localhost:8080
   - Check that the extension has permissions to access localhost

3. **Inspect Network Requests**:
   - In Chrome DevTools, go to the Network tab
   - Submit a query from the extension
   - Look for a request to `/api/query` and check its status and response

4. **Check Backend Logs**:
   - Review the Spring Boot console output for any errors
   - Look for messages related to OpenAI API calls

5. **Verify CORS Settings**:
   - If you see CORS errors in the console, ensure the backend has properly configured CORS settings

## Common Issues and Solutions

1. **"Failed to connect to the AI service"**:
   - Make sure the backend is running
   - Check that the URL in the extension settings is correct (default: http://localhost:8080)

2. **"Failed to get a response from the AI"**:
   - Check your OpenAI API key
   - Look for errors in the backend logs
   - Verify that your OpenAI account has sufficient quota

3. **Extension not appearing in Chrome**:
   - Make sure you've loaded the extension correctly
   - Try reloading the extension from the extensions page

4. **Backend not starting**:
   - Check that all dependencies are resolved
   - Make sure the application.properties file contains valid configuration
