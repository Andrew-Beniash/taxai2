# Tax Law Knowledge Base

This component implements the database and indexing system for the AI-powered tax law assistant. It provides:

1. A SQLite database schema for storing tax law documents
2. Tools for loading and processing tax documents
3. Vector indexing for efficient semantic search

## Files

- `schema.sql` - Database schema definition for tax law documents
- `data_loader.py` - Tool for loading tax law documents into the database
- `index_manager.py` - Manager for FAISS indexes and semantic search
- `requirements.txt` - Python dependencies

## Usage

### Setting up the database

```bash
# Initialize the database
sqlite3 tax_law.db < schema.sql
```

### Loading documents

```bash
# Load a single file
python data_loader.py --source /path/to/document.pdf --db tax_law.db --type file

# Load all documents in a directory
python data_loader.py --source /path/to/documents/ --db tax_law.db --type directory

# Load from URL
python data_loader.py --source https://www.irs.gov/pub/irs-pdf/p17.pdf --db tax_law.db --type url
```

### Creating and using indexes

```bash
# Create a new index
python index_manager.py --db tax_law.db --operation create --name default --type flat

# Update an existing index with new documents
python index_manager.py --db tax_law.db --operation update --name default

# Rebuild an index from scratch
python index_manager.py --db tax_law.db --operation rebuild --name default --type hnsw

# Search using an index
python index_manager.py --db tax_law.db --operation search --name default --query "tax deduction for home office" --limit 5

# List all indexes
python index_manager.py --db tax_law.db --operation list
```

## Database Schema

The system uses several interconnected tables:

- `tax_documents` - Core table for document storage
- `document_sections` - Stores document segments for more granular retrieval
- `tags` - Classification tags for documents
- `document_tags` - Junction table linking documents to tags
- `citations` - Tracks references between documents
- `vector_indexes` - Metadata about FAISS indexes

## Vector Indexing

The system uses FAISS for efficient vector similarity search, with several index types:

- `flat` - Exact search (slower but most accurate)
- `ivf` - Inverted file index (faster with slight accuracy tradeoff)
- `hnsw` - Hierarchical navigable small world graph (very fast approximate search)

## Integration with the RAG System

This knowledge base component integrates with the retrieval-augmented generation (RAG) system by:

1. Providing a database of authoritative tax law documents
2. Enabling semantic search via vector embeddings
3. Supplying document metadata for accurate citation
