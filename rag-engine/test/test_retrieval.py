#!/usr/bin/env python3
"""
Test script for the retrieval pipeline.
This script tests the various components of the retrieval pipeline.
"""

import os
import sys
import logging
import argparse
import time
import json
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.embedding.embedding_model import EmbeddingModel
from src.retrieval.retrieval_pipeline import RetrievalPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_embedding_model():
    """Test the embedding model"""
    logger.info("Testing embedding model...")
    
    # Initialize the model
    model = EmbeddingModel(
        model_name="all-MiniLM-L6-v2",
        use_onnx=True,
        device="cpu"
    )
    
    # Test texts
    texts = [
        "What are the tax implications of cryptocurrency?",
        "How does the IRS treat virtual currency for tax purposes?",
        "Are crypto transactions taxable events?"
    ]
    
    # Generate embeddings
    start_time = time.time()
    embeddings = model.embed_text(texts)
    end_time = time.time()
    
    # Print results
    logger.info(f"Generated {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
    logger.info(f"Embedding time: {end_time - start_time:.3f} seconds")
    
    # Test the similarity between embeddings
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    
    sim_matrix = cosine_similarity(embeddings)
    logger.info(f"Similarity matrix:\n{sim_matrix}")
    
    return model

def test_retrieval_pipeline(model=None, query=None):
    """Test the retrieval pipeline"""
    logger.info("Testing retrieval pipeline...")
    
    # Initialize the pipeline
    pipeline = RetrievalPipeline(
        embedding_model=model,
        model_name="all-MiniLM-L6-v2",
        use_onnx=True,
        faiss_index_path="data/tax_law_index.faiss",
        metadata_path="data/tax_law_docs.csv",
        top_k=5
    )
    
    # Process query
    if query is None:
        query = "What are the tax implications of cryptocurrency?"
    
    logger.info(f"Processing query: {query}")
    result = pipeline.process_query(query)
    
    # Print results
    logger.info(f"Processing time: {result['processing_time']:.3f} seconds")
    logger.info(f"Found {len(result['documents'])} similar documents")
    
    return result

def main():
    """Main entry point for testing"""
    parser = argparse.ArgumentParser(description='Test the retrieval pipeline')
    parser.add_argument('--embedding-only', action='store_true', help='Test only the embedding model')
    parser.add_argument('--pipeline-only', action='store_true', help='Test only the retrieval pipeline')
    parser.add_argument('--query', type=str, help='Query to process')
    parser.add_argument('--output', type=str, help='Output file for results')
    
    args = parser.parse_args()
    
    model = None
    result = None
    
    # Test embedding model
    if not args.pipeline_only:
        model = test_embedding_model()
    
    # Test retrieval pipeline
    if not args.embedding_only:
        result = test_retrieval_pipeline(model, args.query)
    
    # Save results to file
    if args.output and result:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
