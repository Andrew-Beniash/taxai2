#!/bin/bash

# run-tests.sh - Script to run browser extension UI tests
# 
# This script automates the process of building the extension and running tests.
# It ensures the extension is properly built before tests run.

# Set up error handling
set -e

# Define paths
PROJECT_ROOT="/Users/andreibeniash/Desktop/taxai"
EXTENSION_DIR="$PROJECT_ROOT/browser-extension"
TEST_DIR="$PROJECT_ROOT/tests/browser-tests"

# Print information
echo "=== Running Tax AI Browser Extension Tests ==="
echo "Extension directory: $EXTENSION_DIR"
echo "Test directory: $TEST_DIR"

# Build the extension (if needed)
if [ "$1" != "--skip-build" ]; then
  echo -e "\n=== Building the extension ==="
  cd "$EXTENSION_DIR"
  # Check if npm is available
  if command -v npm &> /dev/null; then
    npm run build
  else
    echo "Error: npm not found. Please install Node.js and npm."
    exit 1
  fi
fi

# Navigate to test directory
cd "$TEST_DIR"

# Install test dependencies if needed
if [ ! -d "node_modules" ]; then
  echo -e "\n=== Installing test dependencies ==="
  npm install
fi

# Run the tests
echo -e "\n=== Running UI tests ==="
npm test

# Print completion message
echo -e "\n=== Testing completed ==="