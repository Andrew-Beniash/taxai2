#!/bin/bash
# Setup script for the RAG engine
# This script initializes the data directories, installs Python dependencies,
# and prepares the build environment for C++ components.

set -e

echo "Setting up RAG Engine..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Initialize data directories
echo "Initializing data directories..."
python init_data_dirs.py

# Create build directory for C++ components
echo "Setting up C++ build environment..."
mkdir -p build
cd build
cmake ..
echo "Build environment ready. Use 'cd build && make' to build C++ components."

echo "Setup complete!"
echo "Run 'source venv/bin/activate' to activate the virtual environment."
echo "Run 'python -m src.retrieval.retrieval_pipeline --query \"YOUR QUERY\"' to test the retrieval pipeline."
echo "Run 'python -m src.retrieval.retrieval_pipeline --api' to start the API server."
