"""
retrieval_pipeline.py

This module implements the core retrieval pipeline for the tax law RAG system.
It coordinates the embedding generation, FAISS search, and AI response generation
to provide accurate and factual responses to tax law queries with proper citations.

Key features:
- End-to-end query processing from user input to AI response
- Integration with embedding model and FAISS vector search
- Retrieval of relevant tax law snippets with citation metadata
- Structured output for easy integration with the backend API
"""

import os
import json
import sys
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
import ctypes
from pathlib import Path
import time
import requests

# Add embedding module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from embedding.embedding_model import EmbeddingModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RetrievalPipeline:
    """
    End-to-end retrieval pipeline for tax law queries.
    
    This class coordinates:
    1. Query embedding generation
    2. Vector search using FAISS
    3. Document retrieval with metadata
    4. Response generation with OpenAI
    """
    
    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        model_name: str = "all-MiniLM-L6-v2",
        use_onnx: bool = True,
        faiss_index_path: str = "data/tax_law_index.faiss",
        metadata_path: str = "data/tax_law_docs.csv",
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o",
        top_k: int = 5,
        device: str = "cpu"
    ):
        """
        Initialize the retrieval pipeline.
        
        Args:
            embedding_model: Pre-initialized EmbeddingModel or None to create a new one
            model_name: Name of the sentence-transformers model (if creating new)
            use_onnx: Whether to use ONNX for embedding inference
            faiss_index_path: Path to the FAISS index file
            metadata_path: Path to the document metadata file
            openai_api_key: OpenAI API key for response generation
            openai_model: OpenAI model to use for response generation
            top_k: Number of similar documents to retrieve
            device: Device to use for embedding model
        """
        # Store configuration
        self.faiss_index_path = faiss_index_path
        self.metadata_path = metadata_path
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.openai_model = openai_model
        self.top_k = top_k
        
        # Initialize embedding model if not provided
        if embedding_model is None:
            logger.info(f"Initializing new embedding model: {model_name}")
            self.embedding_model = EmbeddingModel(
                model_name=model_name,
                use_onnx=use_onnx,
                device=device
            )
        else:
            logger.info("Using provided embedding model")
            self.embedding_model = embedding_model
        
        # Initialize FAISS Index using C++ bindings
        self._init_faiss_bindings()
        
        # Load document metadata
        self._load_metadata()
    
    def _init_faiss_bindings(self):
        """Initialize the C++ FAISS bindings"""
        try:
            # Determine the library path based on OS
            if sys.platform.startswith('linux'):
                lib_ext = '.so'
            elif sys.platform == 'darwin':
                lib_ext = '.dylib'
            elif sys.platform == 'win32':
                lib_ext = '.dll'
            else:
                raise RuntimeError(f"Unsupported platform: {sys.platform}")
            
            # Find the FAISS library
            lib_name = f"faiss_wrapper{lib_ext}"
            
            # Check standard locations
            search_paths = [
                os.path.dirname(os.path.abspath(__file__)),  # Current directory
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # Parent directory
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"),  # lib directory
                "/usr/local/lib",
                "/usr/lib",
            ]
            
            lib_path = None
            for path in search_paths:
                candidate = os.path.join(path, lib_name)
                if os.path.exists(candidate):
                    lib_path = candidate
                    break
            
            if lib_path is None:
                raise FileNotFoundError(f"Could not find FAISS wrapper library: {lib_name}")
            
            logger.info(f"Loading FAISS wrapper library from: {lib_path}")
            
            # Load the library
            self.faiss_lib = ctypes.CDLL(lib_path)
            
            # Define function prototypes
            
            # Create FAISS index
            self.faiss_lib.CreateVectorSearch.argtypes = [
                ctypes.c_int,  # dimension
                ctypes.c_char_p,  # index_type
            ]
            self.faiss_lib.CreateVectorSearch.restype = ctypes.c_void_p
            
            # Load index from file
            self.faiss_lib.LoadIndex.argtypes = [
                ctypes.c_void_p,  # vector_search_ptr
                ctypes.c_char_p,  # filename
            ]
            self.faiss_lib.LoadIndex.restype = ctypes.c_bool
            
            # Search for similar vectors
            self.faiss_lib.Search.argtypes = [
                ctypes.c_void_p,  # vector_search_ptr
                ctypes.POINTER(ctypes.c_float),  # query_vector
                ctypes.c_int,  # k
                ctypes.POINTER(ctypes.c_float),  # distances
                ctypes.POINTER(ctypes.c_int64),  # indices
            ]
            self.faiss_lib.Search.restype = ctypes.c_bool
            
            # Get index size
            self.faiss_lib.GetSize.argtypes = [ctypes.c_void_p]
            self.faiss_lib.GetSize.restype = ctypes.c_size_t
            
            # Destroy FAISS index
            self.faiss_lib.DestroyVectorSearch.argtypes = [ctypes.c_void_p]
            
            # Create and load index
            self.vector_search_ptr = self.faiss_lib.CreateVectorSearch(
                self.embedding_model.get_embedding_dimension(),
                "flat".encode('utf-8')
            )
            
            # Check if index file exists before loading
            if os.path.exists(self.faiss_index_path):
                logger.info(f"Loading FAISS index from {self.faiss_index_path}")
                success = self.faiss_lib.LoadIndex(
                    self.vector_search_ptr,
                    self.faiss_index_path.encode('utf-8')
                )
                
                if not success:
                    logger.warning(f"Failed to load FAISS index from {self.faiss_index_path}")
                else:
                    size = self.faiss_lib.GetSize(self.vector_search_ptr)
                    logger.info(f"Loaded FAISS index with {size} vectors")
            else:
                logger.warning(f"FAISS index not found at {self.faiss_index_path}")
        
        except Exception as e:
            logger.error(f"Failed to initialize FAISS bindings: {str(e)}")
            raise
    
    def _load_metadata(self):
        """Load document metadata from CSV file"""
        if not os.path.exists(self.metadata_path):
            logger.warning(f"Metadata file not found at {self.metadata_path}")
            self.metadata = {}
            return
        
        try:
            logger.info(f"Loading metadata from {self.metadata_path}")
            
            # Simple CSV parsing
            metadata = {}
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                # Skip header
                header = f.readline().strip()
                
                for line in f:
                    # Basic CSV parsing (doesn't handle all edge cases)
                    parts = line.strip().split(',', 1)  # Split only at first comma
                    if len(parts) != 2:
                        continue
                    
                    id_str, rest = parts
                    try:
                        id = int(id_str)
                    except ValueError:
                        continue
                    
                    # Extract remaining fields
                    # This is a simplified approach; a proper CSV parser would be better
                    fields = []
                    field = ""
                    in_quotes = False
                    
                    for char in rest:
                        if char == '"':
                            in_quotes = not in_quotes
                        elif char == ',' and not in_quotes:
                            fields.append(field)
                            field = ""
                        else:
                            field += char
                    
                    fields.append(field)  # Add the last field
                    
                    # Remove quotes from fields
                    fields = [f.strip('"') for f in fields]
                    
                    if len(fields) >= 3:
                        doc_id, title, section = fields[0:3]
                        snippet = fields[3] if len(fields) > 3 else ""
                        
                        metadata[id] = {
                            'doc_id': doc_id,
                            'title': title,
                            'section': section,
                            'snippet': snippet
                        }
            
            self.metadata = metadata
            logger.info(f"Loaded metadata for {len(metadata)} documents")
        
        except Exception as e:
            logger.error(f"Failed to load metadata: {str(e)}")
            self.metadata = {}
    
    def process_query(self, query_text: str) -> Dict[str, Any]:
        """
        Process a user query and return relevant documents and AI response.
        
        Args:
            query_text: User query text
            
        Returns:
            Dictionary with query results and AI response
        """
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.embedding_model.embed_text([query_text])[0]
        
        # Search for similar documents
        similar_docs = self._search_similar_documents(query_embedding)
        
        # Generate AI response with citations
        response = self._generate_ai_response(query_text, similar_docs)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Return complete result
        return {
            'query': query_text,
            'documents': similar_docs,
            'response': response,
            'processing_time': processing_time
        }
    
    def _search_similar_documents(self, query_embedding: np.ndarray) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.
        
        Args:
            query_embedding: Query embedding vector
            
        Returns:
            List of similar documents with metadata
        """
        # Prepare query vector
        query_vector = query_embedding.astype(np.float32)
        
        # Prepare output arrays
        distances = np.zeros(self.top_k, dtype=np.float32)
        indices = np.zeros(self.top_k, dtype=np.int64)
        
        # Create ctypes pointers
        distances_ptr = distances.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        indices_ptr = indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int64))
        query_ptr = query_vector.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        
        # Perform search
        success = self.faiss_lib.Search(
            self.vector_search_ptr,
            query_ptr,
            self.top_k,
            distances_ptr,
            indices_ptr
        )
        
        if not success:
            logger.error("FAISS search failed")
            return []
        
        # Process results
        similar_docs = []
        for i in range(self.top_k):
            if indices[i] < 0 or distances[i] == float('inf'):  # Invalid index
                continue
                
            doc_id = int(indices[i])
            distance = float(distances[i])
            
            # Look up metadata
            metadata = self.metadata.get(doc_id, {})
            if not metadata:
                continue
            
            # Add to results
            similar_docs.append({
                'id': doc_id,
                'distance': distance,
                'doc_id': metadata.get('doc_id', f"Unknown-{doc_id}"),
                'title': metadata.get('title', 'Unknown Title'),
                'section': metadata.get('section', ''),
                'snippet': metadata.get('snippet', ''),
                'similarity': 1.0 / (1.0 + distance)  # Convert distance to similarity score
            })
        
        return similar_docs
    
    def _generate_ai_response(
        self, 
        query: str, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate an AI response to the query using retrieved documents.
        
        Args:
            query: User query
            documents: Retrieved similar documents
            
        Returns:
            Response object with answer and citations
        """
        if not documents:
            return {
                'answer': "I couldn't find relevant tax law information to answer your query.",
                'citations': []
            }
        
        # Check if OpenAI API key is available
        if not self.openai_api_key:
            logger.warning("OpenAI API key not provided. Using mock response.")
            return self._generate_mock_response(query, documents)
        
        try:
            # Format context for OpenAI
            context = ""
            for i, doc in enumerate(documents):
                context += f"\n### Document {i+1}: {doc['title']}\n"
                context += f"Source: {doc['doc_id']}, Section: {doc['section']}\n"
                context += f"Text: {doc['snippet']}\n"
            
            # Construct system prompt
            system_prompt = f"""You are an AI tax law assistant. Answer the user's query based on the provided tax law documents.
Use the provided documents to give accurate, factual responses about tax law.
If the documents don't contain enough information to answer the question, acknowledge that you don't have sufficient information.
Always cite your sources using [Document X] notation where X is the document number.
Make your response concise and accurate.

Here are the relevant tax law documents to help answer the user's query:
{context}"""
            
            # Make OpenAI API call
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            payload = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            response_data = response.json()
            
            if 'error' in response_data:
                logger.error(f"OpenAI API error: {response_data['error']}")
                return self._generate_mock_response(query, documents)
            
            answer = response_data['choices'][0]['message']['content']
            
            # Extract citations
            citations = []
            for i, doc in enumerate(documents):
                if f"[Document {i+1}]" in answer:
                    citations.append({
                        'document_number': i+1,
                        'doc_id': doc['doc_id'],
                        'title': doc['title'],
                        'section': doc['section'],
                        'snippet': doc['snippet'][:100] + "..."  # Truncate for brevity
                    })
            
            return {
                'answer': answer,
                'citations': citations
            }
        
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return self._generate_mock_response(query, documents)
    
    def _generate_mock_response(
        self, 
        query: str, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a mock response when OpenAI is not available.
        
        Args:
            query: User query
            documents: Retrieved similar documents
            
        Returns:
            Mock response with answer and citations
        """
        # Create a simple response based on the retrieved documents
        if not documents:
            return {
                'answer': "I couldn't find relevant tax law information to answer your query.",
                'citations': []
            }
        
        # Extract most relevant document
        doc = documents[0]
        
        answer = f"Based on {doc['title']} (Section: {doc['section']}), I found this information that might help: {doc['snippet']}"
        
        # Add citations for up to 3 documents
        citations = []
        for i, doc in enumerate(documents[:3]):
            citations.append({
                'document_number': i+1,
                'doc_id': doc['doc_id'],
                'title': doc['title'],
                'section': doc['section'],
                'snippet': doc['snippet'][:100] + "..."  # Truncate for brevity
            })
        
        return {
            'answer': answer,
            'citations': citations
        }
    
    def __del__(self):
        """Clean up resources when the object is destroyed"""
        if hasattr(self, 'faiss_lib') and hasattr(self, 'vector_search_ptr'):
            try:
                self.faiss_lib.DestroyVectorSearch(self.vector_search_ptr)
                logger.info("Cleaned up FAISS resources")
            except Exception as e:
                logger.error(f"Error cleaning up FAISS resources: {str(e)}")


class APIHandler:
    """
    API handler for the retrieval pipeline.
    
    This class provides a REST API for the retrieval pipeline.
    """
    
    def __init__(
        self,
        pipeline: RetrievalPipeline,
        host: str = "0.0.0.0",
        port: int = 5000
    ):
        """
        Initialize the API handler.
        
        Args:
            pipeline: Retrieval pipeline instance
            host: Host to bind the API server
            port: Port to bind the API server
        """
        self.pipeline = pipeline
        self.host = host
        self.port = port
    
    def start(self):
        """Start the API server"""
        try:
            from flask import Flask, request, jsonify
            
            app = Flask(__name__)
            
            @app.route('/api/query', methods=['POST'])
            def query():
                data = request.json
                
                if not data or 'query' not in data:
                    return jsonify({'error': 'Missing query parameter'}), 400
                
                query_text = data['query']
                
                try:
                    result = self.pipeline.process_query(query_text)
                    return jsonify(result), 200
                except Exception as e:
                    logger.error(f"Error processing query: {str(e)}")
                    return jsonify({'error': str(e)}), 500
            
            @app.route('/api/health', methods=['GET'])
            def health():
                return jsonify({'status': 'ok'}), 200
            
            logger.info(f"Starting API server on {self.host}:{self.port}")
            app.run(host=self.host, port=self.port)
        
        except Exception as e:
            logger.error(f"Failed to start API server: {str(e)}")
            raise


# Command-line interface for testing
def main():
    """Main entry point for testing the retrieval pipeline"""
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='RAG-based tax law retrieval system')
    parser.add_argument('--query', '-q', type=str, help='Query to process')
    parser.add_argument('--model', '-m', type=str, default='all-MiniLM-L6-v2', help='Embedding model name')
    parser.add_argument('--index', '-i', type=str, default='data/tax_law_index.faiss', help='FAISS index path')
    parser.add_argument('--metadata', '-d', type=str, default='data/tax_law_docs.csv', help='Metadata path')
    parser.add_argument('--api', '-a', action='store_true', help='Start API server')
    parser.add_argument('--port', '-p', type=int, default=5000, help='API server port')
    
    args = parser.parse_args()
    
    # Initialize the pipeline
    pipeline = RetrievalPipeline(
        model_name=args.model,
        faiss_index_path=args.index,
        metadata_path=args.metadata
    )
    
    # Process query or start API
    if args.api:
        # Start API server
        api = APIHandler(pipeline, port=args.port)
        api.start()
    elif args.query:
        # Process query
        result = pipeline.process_query(args.query)
        
        # Print results
        print("\n=== Query Results ===")
        print(f"Query: {result['query']}")
        print(f"Processing time: {result['processing_time']:.3f} seconds")
        
        print("\n=== Similar Documents ===")
        for i, doc in enumerate(result['documents']):
            print(f"Document {i+1}: {doc['title']} (Source: {doc['doc_id']})")
            print(f"Section: {doc['section']}")
            print(f"Similarity: {doc['similarity']:.4f}")
            print(f"Snippet: {doc['snippet'][:100]}...")
            print()
        
        print("\n=== AI Response ===")
        print(result['response']['answer'])
        
        print("\n=== Citations ===")
        for citation in result['response']['citations']:
            print(f"[{citation['document_number']}] {citation['title']} - {citation['section']}")
    else:
        print("Please provide a query using --query or start the API server using --api")


if __name__ == "__main__":
    main()
