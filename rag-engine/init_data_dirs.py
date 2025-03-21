#!/usr/bin/env python3
"""
Script to initialize the data directories for the RAG engine.
This creates the necessary directory structure and placeholder files.
"""

import os
import argparse
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Initialize the data directories"""
    parser = argparse.ArgumentParser(description='Initialize RAG Engine data directories')
    parser.add_argument('--data-dir', type=str, default='data', help='Data directory')
    parser.add_argument('--models-dir', type=str, default='models', help='Models directory')
    args = parser.parse_args()
    
    # Create data directory
    logger.info(f"Creating data directory: {args.data_dir}")
    os.makedirs(args.data_dir, exist_ok=True)
    
    # Create models directory
    logger.info(f"Creating models directory: {args.models_dir}")
    os.makedirs(args.models_dir, exist_ok=True)
    
    # Create placeholder README files
    with open(os.path.join(args.data_dir, 'README.md'), 'w') as f:
        f.write("""# RAG Engine Data Directory

This directory contains data files for the RAG engine:

- `tax_law_index.faiss` - FAISS index file for similarity search
- `tax_law_docs.csv` - Document metadata file
- Other data files for the RAG engine

Note: These files will be created automatically when the system processes tax law documents.
""")
    
    with open(os.path.join(args.models_dir, 'README.md'), 'w') as f:
        f.write("""# RAG Engine Models Directory

This directory contains model files for the RAG engine:

- ONNX model files for sentence transformers
- Configuration files for embedding models
- Other model-related files

Note: These files will be created automatically when the system initializes the embedding models.
""")
    
    # Create a sample configuration file
    config = {
        "embedding": {
            "model_name": "all-MiniLM-L6-v2",
            "use_onnx": True,
            "device": "cpu"
        },
        "faiss": {
            "index_type": "flat",
            "index_path": os.path.join(args.data_dir, "tax_law_index.faiss"),
            "metadata_path": os.path.join(args.data_dir, "tax_law_docs.csv")
        },
        "retrieval": {
            "top_k": 5,
            "openai_model": "gpt-4o"
        },
        "api": {
            "host": "0.0.0.0",
            "port": 5000
        }
    }
    
    config_path = os.path.join(args.data_dir, 'config.json')
    logger.info(f"Creating sample configuration file: {config_path}")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Create empty placeholder files
    placeholder_files = [
        (os.path.join(args.data_dir, '.gitkeep'), ''),
        (os.path.join(args.models_dir, '.gitkeep'), '')
    ]
    
    for path, content in placeholder_files:
        logger.info(f"Creating placeholder file: {path}")
        with open(path, 'w') as f:
            f.write(content)
    
    logger.info("Initialization complete!")
    logger.info(f"Data directory: {os.path.abspath(args.data_dir)}")
    logger.info(f"Models directory: {os.path.abspath(args.models_dir)}")
    logger.info(f"Configuration file: {os.path.abspath(config_path)}")

if __name__ == "__main__":
    main()
