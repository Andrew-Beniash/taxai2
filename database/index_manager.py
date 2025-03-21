#!/usr/bin/env python3
"""
Index Manager for Tax Law Knowledge Base

This module manages the vector index for tax documents, handling:
- Creating and updating FAISS indexes for tax law documents
- Converting document sections to vector embeddings
- Providing an API for efficient semantic search
- Integrating with the RAG system

Usage:
    python index_manager.py --db [database_file] --operation [create|update|search]
"""

import argparse
import sqlite3
import os
import json
import numpy as np
import logging
import sys
import pickle
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Union
import faiss
from sentence_transformers import SentenceTransformer
import onnxruntime as ort
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("index_manager.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("index_manager")

# Database connection helper
def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

class ONNXEmbedder:
    """ONNX-based text embedder for efficient vector generation."""
    
    def __init__(self, model_path: str):
        """Initialize with path to ONNX model."""
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        
    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode text to embeddings using ONNX runtime."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            inputs = {self.input_name: batch}
            embeddings = self.session.run(None, inputs)[0]
            all_embeddings.append(embeddings)
            
        return np.vstack(all_embeddings)

class SentenceTransformerEmbedder:
    """SentenceTransformer-based text embedder."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize with model name."""
        self.model = SentenceTransformer(model_name)
        
    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode text to embeddings using SentenceTransformer."""
        return self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    
    def export_to_onnx(self, output_path: str) -> str:
        """Export model to ONNX format for faster inference."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.model.export_to_onnx(output_path)
        return output_path

class IndexManager:
    """Manager for FAISS indexes of tax law documents."""
    
    def __init__(self, db_path: str, index_dir: str = 'indexes'):
        """Initialize with database path and index directory."""
        self.db_path = db_path
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)
        
        # Default to SentenceTransformer for embeddings
        self.embedder = SentenceTransformerEmbedder()
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
        
        # Try to export to ONNX for better performance
        try:
            onnx_path = os.path.join(index_dir, 'embedder.onnx')
            if not os.path.exists(onnx_path):
                self.embedder.export_to_onnx(onnx_path)
                logger.info(f"Exported embedding model to ONNX: {onnx_path}")
            
            # Switch to ONNX embedder if available
            if os.path.exists(onnx_path):
                self.embedder = ONNXEmbedder(onnx_path)
                logger.info(f"Using ONNX embedder for better performance")
        except Exception as e:
            logger.warning(f"Could not use ONNX embedder, falling back to SentenceTransformer: {str(e)}")
    
    def create_index(self, name: str = 'default', index_type: str = 'flat') -> None:
        """Create a new FAISS index for document sections."""
        conn = get_db_connection(self.db_path)
        
        try:
            # Check if index already exists
            cursor = conn.execute(
                'SELECT id FROM vector_indexes WHERE index_name = ?',
                (name,)
            )
            if cursor.fetchone():
                logger.warning(f"Index {name} already exists. Use update_index instead.")
                return
            
            # Get all document sections
            cursor = conn.execute('''
                SELECT s.id, s.document_id, s.section_number, s.section_title, s.content,
                       d.title, d.source, d.document_type
                FROM document_sections s
                JOIN tax_documents d ON s.document_id = d.id
                WHERE d.is_active = 1
            ''')
            
            sections = cursor.fetchall()
            logger.info(f"Creating index from {len(sections)} document sections")
            
            if not sections:
                logger.warning("No document sections found to index")
                return
                
            # Prepare text for embedding
            texts = []
            metadata = []
            for section in sections:
                # Combine section data for better embedding context
                section_text = f"{section['title']} - {section['section_title'] or section['section_number']}:\n{section['content']}"
                texts.append(section_text)
                
                # Store metadata for retrieval
                metadata.append({
                    'section_id': section['id'],
                    'document_id': section['document_id'],
                    'title': section['title'],
                    'section_title': section['section_title'],
                    'section_number': section['section_number'],
                    'source': section['source'],
                    'document_type': section['document_type']
                })
            
            # Create embeddings
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.embedder.encode(texts)
            dim = embeddings.shape[1]
            self.embedding_dim = dim
            
            # Create FAISS index
            if index_type == 'flat':
                # Simple flat index (most accurate but slower for large collections)
                index = faiss.IndexFlatL2(dim)
            elif index_type == 'ivf':
                # IVF index for larger collections (faster search with slight accuracy trade-off)
                # Determine number of clusters (rule of thumb: sqrt of num vectors)
                nlist = min(int(np.sqrt(len(texts))), 100)  # Cap at 100 clusters
                quantizer = faiss.IndexFlatL2(dim)
                index = faiss.IndexIVFFlat(quantizer, dim, nlist)
                # Need to train IVF index
                index.train(embeddings)
            elif index_type == 'hnsw':
                # HNSW index for very fast approximate search
                index = faiss.IndexHNSWFlat(dim, 32)  # 32 neighbors per node
            else:
                raise ValueError(f"Unsupported index type: {index_type}")
            
            # Add vectors to index
            index.add(embeddings)
            
            # Save index and metadata
            index_path = os.path.join(self.index_dir, f"{name}.index")
            metadata_path = os.path.join(self.index_dir, f"{name}_metadata.pkl")
            
            faiss.write_index(index, index_path)
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            # Register index in database
            now = datetime.now().isoformat()
            conn.execute(
                '''INSERT INTO vector_indexes 
                   (index_name, dimension, index_type, index_path, created_date, 
                    document_count, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (name, dim, index_type, index_path, now, len(sections), now)
            )
            conn.commit()
            
            logger.info(f"Successfully created index '{name}' with {len(sections)} sections")
            
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            raise
        finally:
            conn.close()
    
    def update_index(self, name: str = 'default') -> None:
        """Update an existing index with new documents."""
        conn = get_db_connection(self.db_path)
        
        try:
            # Check if index exists
            cursor = conn.execute(
                '''SELECT id, index_path, index_type, dimension 
                   FROM vector_indexes WHERE index_name = ?''',
                (name,)
            )
            index_info = cursor.fetchone()
            
            if not index_info:
                logger.warning(f"Index {name} does not exist. Use create_index first.")
                return
            
            index_path = index_info['index_path']
            index_type = index_info['index_type']
            dimension = index_info['dimension']
            
            # Load existing index
            index = faiss.read_index(index_path)
            
            # Load existing metadata
            metadata_path = os.path.join(self.index_dir, f"{name}_metadata.pkl")
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            # Find indexed section IDs
            indexed_section_ids = set(item['section_id'] for item in metadata)
            
            # Get all sections not yet indexed
            placeholders = ','.join('?' for _ in indexed_section_ids) if indexed_section_ids else '0'
            query = f'''
                SELECT s.id, s.document_id, s.section_number, s.section_title, s.content,
                       d.title, d.source, d.document_type
                FROM document_sections s
                JOIN tax_documents d ON s.document_id = d.id
                WHERE d.is_active = 1 AND s.id NOT IN ({placeholders})
            '''
            
            cursor = conn.execute(query, list(indexed_section_ids) if indexed_section_ids else [])
            new_sections = cursor.fetchall()
            
            if not new_sections:
                logger.info("No new sections to index")
                return
            
            logger.info(f"Updating index with {len(new_sections)} new document sections")
            
            # Prepare text for embedding
            texts = []
            new_metadata = []
            for section in new_sections:
                # Combine section data for better embedding context
                section_text = f"{section['title']} - {section['section_title'] or section['section_number']}:\n{section['content']}"
                texts.append(section_text)
                
                # Store metadata for retrieval
                new_metadata.append({
                    'section_id': section['id'],
                    'document_id': section['document_id'],
                    'title': section['title'],
                    'section_title': section['section_title'],
                    'section_number': section['section_number'],
                    'source': section['source'],
                    'document_type': section['document_type']
                })
            
            # Create embeddings
            embeddings = self.embedder.encode(texts)
            
            # Add vectors to index
            index.add(embeddings)
            
            # Update metadata
            metadata.extend(new_metadata)
            
            # Save updated index and metadata
            faiss.write_index(index, index_path)
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            # Update index info in database
            now = datetime.now().isoformat()
            conn.execute(
                '''UPDATE vector_indexes 
                   SET document_count = ?, last_updated = ?
                   WHERE index_name = ?''',
                (len(metadata), now, name)
            )
            conn.commit()
            
            logger.info(f"Successfully updated index '{name}' with {len(new_sections)} new sections")
            
        except Exception as e:
            logger.error(f"Error updating index: {str(e)}")
            raise
        finally:
            conn.close()
    
    def search(self, query: str, name: str = 'default', k: int = 5) -> List[Dict[str, Any]]:
        """Search the index for sections relevant to the query."""
        conn = get_db_connection(self.db_path)
        
        try:
            # Check if index exists
            cursor = conn.execute(
                'SELECT index_path FROM vector_indexes WHERE index_name = ?',
                (name,)
            )
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Index {name} does not exist")
                return []
                
            index_path = result['index_path']
            
            # Load index
            index = faiss.read_index(index_path)
            
            # Load metadata
            metadata_path = os.path.join(self.index_dir, f"{name}_metadata.pkl")
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            # Encode query
            query_embedding = self.embedder.encode([query])
            
            # Search
            distances, indices = index.search(query_embedding, k)
            
            # Format results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:  # -1 indicates no result found
                    # Get section data
                    section_id = metadata[idx]['section_id']
                    document_id = metadata[idx]['document_id']
                    
                    # Get full section content from database
                    cursor = conn.execute(
                        '''SELECT s.*, d.title as document_title, d.source, d.document_type 
                           FROM document_sections s
                           JOIN tax_documents d ON s.document_id = d.id
                           WHERE s.id = ?''',
                        (section_id,)
                    )
                    section = cursor.fetchone()
                    
                    if section:
                        results.append({
                            'section_id': section_id,
                            'document_id': document_id,
                            'document_title': section['document_title'],
                            'section_title': section['section_title'],
                            'section_number': section['section_number'],
                            'content': section['content'],
                            'source': section['source'],
                            'document_type': section['document_type'],
                            'score': float(1.0 / (1.0 + distances[0][i]))  # Convert distance to similarity score
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []
        finally:
            conn.close()
    
    def rebuild_index(self, name: str = 'default', index_type: str = 'flat') -> None:
        """Rebuild an index from scratch (useful after many updates)."""
        conn = get_db_connection(self.db_path)
        
        try:
            # Check if index exists
            cursor = conn.execute(
                'SELECT id FROM vector_indexes WHERE index_name = ?',
                (name,)
            )
            if cursor.fetchone():
                # Delete existing index
                conn.execute('DELETE FROM vector_indexes WHERE index_name = ?', (name,))
                conn.commit()
                
                # Remove index files
                index_path = os.path.join(self.index_dir, f"{name}.index")
                metadata_path = os.path.join(self.index_dir, f"{name}_metadata.pkl")
                
                if os.path.exists(index_path):
                    os.remove(index_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
            
            # Create new index
            self.create_index(name, index_type)
            logger.info(f"Successfully rebuilt index '{name}'")
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_embedding_for_section(self, section_id: int) -> Optional[np.ndarray]:
        """Get embedding for a specific section (useful for direct storage in DB)."""
        conn = get_db_connection(self.db_path)
        
        try:
            # Get section content
            cursor = conn.execute(
                '''SELECT s.*, d.title 
                   FROM document_sections s
                   JOIN tax_documents d ON s.document_id = d.id
                   WHERE s.id = ?''',
                (section_id,)
            )
            section = cursor.fetchone()
            
            if not section:
                logger.warning(f"Section {section_id} not found")
                return None
            
            # Create section text
            section_text = f"{section['title']} - {section['section_title'] or section['section_number']}:\n{section['content']}"
            
            # Generate embedding
            embedding = self.embedder.encode([section_text])[0]
            return embedding
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            return None
        finally:
            conn.close()
    
    def store_section_embedding(self, section_id: int) -> bool:
        """Store embedding directly in the database for a section."""
        conn = get_db_connection(self.db_path)
        
        try:
            # Get embedding
            embedding = self.get_embedding_for_section(section_id)
            
            if embedding is None:
                return False
            
            # Store in database
            embedding_blob = embedding.tobytes()  # Convert numpy array to bytes
            conn.execute(
                'UPDATE document_sections SET embedding = ? WHERE id = ?',
                (embedding_blob, section_id)
            )
            conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            return False
        finally:
            conn.close()
    
    def list_indexes(self) -> List[Dict[str, Any]]:
        """List all available indexes in the database."""
        conn = get_db_connection(self.db_path)
        
        try:
            cursor = conn.execute(
                '''SELECT index_name, dimension, index_type, document_count, 
                   created_date, last_updated
                   FROM vector_indexes'''
            )
            indexes = [dict(row) for row in cursor.fetchall()]
            return indexes
            
        except Exception as e:
            logger.error(f"Error listing indexes: {str(e)}")
            return []
        finally:
            conn.close()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Manage FAISS indexes for tax law documents.')
    parser.add_argument('--db', default='tax_law.db', help='Database file path')
    parser.add_argument('--operation', required=True, 
                        choices=['create', 'update', 'rebuild', 'search', 'list'],
                        help='Operation to perform')
    parser.add_argument('--name', default='default', help='Index name')
    parser.add_argument('--type', default='flat', 
                        choices=['flat', 'ivf', 'hnsw'],
                        help='Index type (for create/rebuild)')
    parser.add_argument('--query', help='Search query (for search operation)')
    parser.add_argument('--limit', type=int, default=5, help='Result limit for search')
    
    args = parser.parse_args()
    
    index_manager = IndexManager(args.db)
    
    if args.operation == 'create':
        index_manager.create_index(args.name, args.type)
        print(f"Created index '{args.name}' of type {args.type}")
        
    elif args.operation == 'update':
        index_manager.update_index(args.name)
        print(f"Updated index '{args.name}'")
        
    elif args.operation == 'rebuild':
        index_manager.rebuild_index(args.name, args.type)
        print(f"Rebuilt index '{args.name}' of type {args.type}")
        
    elif args.operation == 'search':
        if not args.query:
            print("Error: --query is required for search operation")
            return
            
        results = index_manager.search(args.query, args.name, args.limit)
        print(f"Found {len(results)} results for '{args.query}':")
        
        for i, result in enumerate(results):
            print(f"\n--- Result {i+1} (Score: {result['score']:.4f}) ---")
            print(f"Document: {result['document_title']}")
            print(f"Section: {result['section_title'] or result['section_number']}")
            print(f"Source: {result['source']} ({result['document_type']})")
            print(f"Content: {result['content'][:200]}...")  # Show first 200 chars
            
    elif args.operation == 'list':
        indexes = index_manager.list_indexes()
        print(f"Found {len(indexes)} indexes:")
        
        for idx in indexes:
            print(f"\n--- {idx['index_name']} ---")
            print(f"Type: {idx['index_type']}")
            print(f"Dimension: {idx['dimension']}")
            print(f"Documents: {idx['document_count']}")
            print(f"Created: {idx['created_date']}")
            print(f"Last Updated: {idx['last_updated']}")

if __name__ == '__main__':
    main()
