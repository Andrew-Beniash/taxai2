#!/bin/bash
# Run script for the RAG engine API
# This script starts the API server.

set -e

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set OpenAI API key if provided
if [ ! -z "$1" ]; then
    export OPENAI_API_KEY="$1"
fi

# Start the API server
echo "Starting RAG Engine API server..."
python -m src.retrieval.retrieval_pipeline --api

# Note: The server will run in the foreground. 
# Press Ctrl+C to stop the server.
