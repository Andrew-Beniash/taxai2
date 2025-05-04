# Testing OpenAI Integration

This document provides instructions for verifying that the OpenAI API integration is working correctly in the Tax Law Assistant project.

## Prerequisites

1. You need a valid OpenAI API key
2. The backend service must be running
3. Your API key must be properly configured

## Setting Up Your API Key

The system reads your OpenAI API key from the `OPENAI_API_KEY` environment variable. Before testing, make sure to set this variable:

```bash
# For macOS/Linux
export OPENAI_API_KEY=your_api_key_here

# For Windows Command Prompt
set OPENAI_API_KEY=your_api_key_here

# For Windows PowerShell
$env:OPENAI_API_KEY = "your_api_key_here"
```

## Method 1: Using the Test Script

1. Make the test script executable:
   ```bash
   chmod +x test-openai.sh
   ```

2. Run the test script:
   ```bash
   ./test-openai.sh
   ```

3. Check the output. If you see a JSON response with a reasonable answer to the tax question, the integration is working.

## Method 2: Using the Test Endpoint

You can also test the integration by sending a direct request to the test endpoint:

```bash
curl -X POST http://localhost:8080/api/test/openai \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the standard tax deductions for 2024?"}'
```

## Method 3: Using the OpenAITester Utility

The project includes a standalone Java utility to test the OpenAI integration:

```bash
# Make the script executable
chmod +x run-openai-test.sh

# Run the test utility
./run-openai-test.sh
```

The utility will prompt you for your API key if one is not set in the environment variables, and then make a test query to the OpenAI API.

## Method 4: Using the Application UI

If you have the browser extension installed:

1. Click on the extension icon
2. Enter a tax-related question in the query box
3. Submit the query
4. If you get a coherent response, the OpenAI integration is working

## Troubleshooting

If the integration is not working, check the following:

1. **API Key**: Ensure your OpenAI API key is correct and has not expired
2. **Backend Service**: Verify that the backend service is running (`http://localhost:8080`)
3. **Logs**: Check the logs at `backend/logs/taxlaw-api.log` for error messages
4. **Network**: Ensure your network allows connections to the OpenAI API
5. **API Quota**: Check if you've exceeded your OpenAI API usage limits

## Running Automated Tests

We also have automated tests for the OpenAI integration:

```bash
cd backend
./mvnw test -Dtest=OpenAIServiceTest
```

If all tests pass, the basic functionality of the OpenAI service is working correctly.

## Common Issues

1. **"Authorization failed" error**: Your API key is missing or incorrect
2. **Timeout errors**: OpenAI API may be experiencing high load or your internet connection is slow
3. **"No response from API" error**: Check your network connection
4. **Empty or error responses**: The API key might have insufficient permissions or quota

For further assistance, contact the development team.
