#!/bin/bash
# Script to compile and run the OpenAITester class
# Make this script executable with: chmod +x run-openai-test.sh

# Change to the backend directory
cd "$(dirname "$0")/backend" || exit 1

echo "Compiling OpenAITester..."
./mvnw compile

echo "Running OpenAITester..."
./mvnw exec:java -Dexec.mainClass="com.ai.taxlaw.util.OpenAITester"

echo "Test completed."
