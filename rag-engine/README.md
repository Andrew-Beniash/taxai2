# RAG Engine for Tax Law Assistant

This component provides the Retrieval-Augmented Generation (RAG) engine for the tax law assistant. It includes a high-performance vector search implementation using FAISS, text embedding using sentence-transformers, and a query pipeline that connects to OpenAI models for response generation.

## Features

- High-performance FAISS indexing for similarity search (implemented in C++)
- ONNX-accelerated text embedding using sentence-transformers
- Retrieval pipeline that retrieves relevant tax law information
- API for integration with the backend service
- Response generation with proper citations

## Components

### Vector Store

The vector store is implemented in C++ using FAISS for maximum performance. It provides:

- Multiple index types (Flat L2, HNSW, IVF)
- Document metadata storage
- Memory-mapped storage for large indices

### Embedding Model

The embedding model converts text to vector embeddings using:

- Sentence Transformers models
- ONNX runtime acceleration
- Batch processing for efficiency

### Retrieval Pipeline

The retrieval pipeline coordinates:

- Query embedding
- Similarity search
- Document retrieval
- Response generation with citations

## Building and Running

### Prerequisites

- C++17 compiler
- CMake 3.10+
- FAISS library
- OpenBLAS
- Python 3.8+
- PyTorch
- ONNX Runtime

### Build Instructions

1. Build the C++ components:

```bash
mkdir build
cd build
cmake ..
make
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Run the retrieval pipeline:

```bash
# Process a query
python -m src.retrieval.retrieval_pipeline --query "What are the tax implications of cryptocurrency?"

# Start the API server
python -m src.retrieval.retrieval_pipeline --api --port 5000
```

## Integration

The RAG engine integrates with the backend service via a REST API. The API endpoints include:

- `/api/query` - Process a query and return relevant documents with AI response
- `/api/health` - Check the health of the service

## Configuration

Configuration options:

- `model_name` - Name of the sentence-transformers model to use
- `use_onnx` - Whether to use ONNX acceleration
- `faiss_index_path` - Path to the FAISS index file
- `metadata_path` - Path to the document metadata file
- `openai_api_key` - OpenAI API key for response generation
- `openai_model` - OpenAI model to use for response generation
- `top_k` - Number of similar documents to retrieve
