#!/bin/bash
# Make this script executable with: chmod +x test-openai.sh

# Set your OpenAI API key
# If you don't want to store your API key in the script, you can export it before running:
# export OPENAI_API_KEY=your_api_key_here

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set."
    echo "Please set your OpenAI API key using:"
    echo "export OPENAI_API_KEY=your_api_key_here"
    exit 1
fi

# Request to test the OpenAI integration
echo "Testing OpenAI integration..."
curl -X POST http://localhost:8080/api/test/openai \
  -H "Content-Type: application/json" \
  -d '{"query":"Explain the standard deduction for 2024"}' \
  | json_pp

echo -e "\n\nIf you see a proper response above, the OpenAI integration is working!"
