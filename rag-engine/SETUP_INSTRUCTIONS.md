# RAG Engine Setup Instructions

## Initial Setup

To set up the RAG engine, follow these steps:

1. Navigate to the rag-engine directory:
   ```bash
   cd /Users/andreibeniash/Desktop/taxai/rag-engine
   ```

2. Make the scripts executable:
   ```bash
   chmod +x setup.sh run.sh init_data_dirs.py
   ```

3. Run the setup script to initialize the environment:
   ```bash
   ./setup.sh
   ```

4. Build the C++ components:
   ```bash
   cd build
   make
   cd ..
   ```

## Running the RAG Engine

To run the RAG engine API server:

```bash
./run.sh [OPENAI_API_KEY]
```

Where `[OPENAI_API_KEY]` is your OpenAI API key. If you don't provide it directly, it will try to use the `OPENAI_API_KEY` environment variable.

## Testing the RAG Engine

To test the RAG engine with a specific query:

```bash
# Activate the virtual environment first
source venv/bin/activate

# Run a test query
python -m src.retrieval.retrieval_pipeline --query "What are the tax implications of cryptocurrency?"
```

## Troubleshooting

If you encounter any issues:

1. Ensure that you have all the required dependencies installed (FAISS, OpenBLAS, etc.)
2. Check the logs for error messages
3. Verify that the OPENAI_API_KEY is set correctly
4. Ensure that the data directories are properly initialized

For more details, refer to the README.md file.
