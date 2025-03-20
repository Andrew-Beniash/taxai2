#!/bin/bash

# A script to build and run the Tax Law Assistant backend locally

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
  echo "ERROR: OPENAI_API_KEY environment variable is not set."
  echo "Please set it with: export OPENAI_API_KEY=your_api_key"
  exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Building the Tax Law Assistant backend..."
mvn clean package -DskipTests

if [ $? -eq 0 ]; then
  echo "Build successful. Starting the application..."
  java -jar target/tax-law-assistant-1.0.0-SNAPSHOT.jar
else
  echo "Build failed. Please check the error messages above."
  exit 1
fi
