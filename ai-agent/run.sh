#!/bin/bash

# Tax Law AI Agent Runner Script

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/downloads
mkdir -p data/processed
mkdir -p data/uploads
mkdir -p data/stats
mkdir -p logs

# Run the AI agent
echo "Starting Tax Law AI Agent..."
python -m src.main "$@"
