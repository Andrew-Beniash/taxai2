"""
Document Indexer Module

This module handles sending processed documents to the RAG system for indexing.
It communicates with the RAG API to update the knowledge base.
"""

import requests
import os
import json
import logging
from datetime import datetime
import time
import glob

class DocumentIndexer:
    """Index processed tax documents in the RAG system"""
    
    def __init__(self, rag_api_url='http://localhost:5000/rag/index'):
        """Initialize with RAG API URL"""
        self.rag_api_url = rag_api_url
        self.processed_dir = 'data/processed'
        self.stats_dir = 'data/stats'
        os.makedirs(self.stats_dir, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('document_indexer')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def index_documents(self, file_paths):
        """Index processed documents in the RAG system"""
        if not file_paths:
            self.logger.info("No documents to index")
            return []
        
        self.logger.info(f"Starting indexing for {len(file_paths)} documents")
        indexed_files = []
        
        for file_path in file_paths:
            try:
                result = self.index_document(file_path)
                if result:
                    indexed_files.append(file_path)
                # Be nice to the RAG API
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error indexing {file_path}: {str(e)}")
        
        # Update index stats
        if indexed_files:
            self._update_index_stats(indexed_files)
        
        self.logger.info(f"Successfully indexed {len(indexed_files)} documents")
        return indexed_files
    
    def index_document(self, file_path):
        """Index a single document in the RAG system"""
        try:
            # Check if document exists
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False
            
            # Get metadata if available
            metadata = self._get_metadata(file_path)
            
            # Read document content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Skip empty documents
            if not content.strip():
                self.logger.warning(f"Empty document, skipping: {file_path}")
                return False
            
            # Prepare payload for RAG API
            payload = {
                'content': content,
                'metadata': metadata
            }
            
            # Send to RAG API
            self.logger.info(f"Sending document to RAG API: {os.path.basename(file_path)}")
            
            # TODO: Uncomment when RAG API is available
            # response = requests.post(self.rag_api_url, json=payload, timeout=60)
            # if response.status_code == 200:
            #     self.logger.info(f"Successfully indexed: {os.path.basename(file_path)}")
            #     return True
            # else:
            #     self.logger.error(f"Failed to index {os.path.basename(file_path)}: {response.text}")
            #     return False
            
            # For testing/development, simulate success
            self.logger.info(f"Successfully indexed (simulated): {os.path.basename(file_path)}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error indexing document {file_path}: {str(e)}")
            return False
    
    def _get_metadata(self, file_path):
        """Get metadata for a document"""
        meta_path = file_path + ".meta.json"
        
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
        else:
            # Create basic metadata if not available
            filename = os.path.basename(file_path)
            metadata = {
                "source": "unknown",
                "document_type": "unknown",
                "file_name": filename,
                "indexed_at": datetime.now().isoformat()
            }
        
        # Add indexing timestamp
        metadata["indexed_at"] = datetime.now().isoformat()
        
        return metadata
    
    def _update_index_stats(self, indexed_files):
        """Update index statistics"""
        stats_file = os.path.join(self.stats_dir, 'index_stats.json')
        
        # Load existing stats or create new
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats = json.load(f)
        else:
            stats = {
                "total_documents": 0,
                "last_update": "",
                "document_types": {}
            }
        
        # Update stats
        timestamp = datetime.now().isoformat()
        stats["last_update"] = timestamp
        stats["total_documents"] += len(indexed_files)
        
        # Update document type counts
        for file_path in indexed_files:
            meta_path = file_path + ".meta.json"
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
                
                doc_type = metadata.get("file_type", "unknown")
                if doc_type in stats["document_types"]:
                    stats["document_types"][doc_type] += 1
                else:
                    stats["document_types"][doc_type] = 1
        
        # Save updated stats
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        self.logger.info(f"Updated index stats: {len(indexed_files)} new documents, {stats['total_documents']} total")
    
    def rebuild_index(self):
        """Rebuild the entire index with all processed documents"""
        self.logger.info("Starting full index rebuild")
        
        # Get all processed files
        processed_files = glob.glob(os.path.join(self.processed_dir, "*.processed.txt"))
        
        if not processed_files:
            self.logger.info("No processed files found for indexing")
            return False
        
        self.logger.info(f"Found {len(processed_files)} files for rebuilding the index")
        
        # TODO: Implement RAG API call to clear existing index
        # requests.post(f"{self.rag_api_url}/clear", timeout=30)
        
        # Index all documents
        indexed_files = self.index_documents(processed_files)
        
        self.logger.info(f"Completed index rebuild with {len(indexed_files)} documents")
        return len(indexed_files) > 0

# Simple test to run if this module is run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    indexer = DocumentIndexer()
    # Find processed files
    processed_files = glob.glob(os.path.join('data/processed', "*.processed.txt"))
    if processed_files:
        indexer.index_documents(processed_files)
    else:
        print("No processed files found to index")
