#!/bin/bash

# Tax Law Fetcher Agent Runner Script
# This script sets up the environment and runs the Tax Law Fetcher agent

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the agent
echo "Starting Tax Law Fetcher Agent..."
python src/main.py

# Deactivate virtual environment on exit
deactivate
