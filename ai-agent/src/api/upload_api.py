"""
Upload API Module

This module provides a REST API for uploading custom documents like firm-specific policies.
It handles document uploads, processing, and indexing into the RAG system.
"""

from flask import Flask, request, jsonify
import os
import logging
import json
import uuid
from datetime import datetime

# Import our components
from src.preprocessing.processor import DocumentProcessor
from src.indexing.indexer import DocumentIndexer

app = Flask(__name__)

# Set up logging
logger = logging.getLogger('upload_api')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize components
processor = DocumentProcessor()
indexer = DocumentIndexer()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "service": "Document Upload API",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/upload', methods=['POST'])
def upload_document():
    """API endpoint for uploading firm-specific documents"""
    if 'file' not in request.files:
        logger.error("No file part in the request")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        logger.error("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    
    # Get metadata from form
    try:
        metadata_str = request.form.get('metadata', '{}')
        metadata = json.loads(metadata_str)
    except json.JSONDecodeError:
        logger.error("Invalid metadata JSON")
        metadata = {}
    
    # Add required metadata fields if missing
    if 'source' not in metadata:
        metadata['source'] = 'Firm'
    
    # Save uploaded file
    upload_dir = 'data/uploads'
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename to avoid collisions
    original_filename = file.filename
    file_extension = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    
    logger.info(f"File saved: {file_path}")
    
    # Save metadata
    metadata['original_filename'] = original_filename
    metadata['upload_time'] = datetime.now().isoformat()
    metadata['uploaded_by'] = request.form.get('user', 'unknown')
    
    metadata_path = file_path + ".meta.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Process file
    try:
        logger.info(f"Processing file: {original_filename}")
        processed_path = processor.process_file(file_path)
        
        if processed_path:
            # Index the processed file
            logger.info(f"Indexing file: {original_filename}")
            success = indexer.index_document(processed_path)
            
            if success:
                logger.info(f"Successfully processed and indexed: {original_filename}")
                return jsonify({
                    'success': True,
                    'message': 'Document uploaded, processed, and indexed successfully',
                    'original_filename': original_filename,
                    'processed_path': processed_path
                }), 200
            else:
                logger.error(f"Failed to index: {original_filename}")
                return jsonify({
                    'success': False,
                    'error': 'Document was processed but indexing failed',
                    'original_filename': original_filename
                }), 500
        else:
            logger.error(f"Failed to process: {original_filename}")
            return jsonify({
                'success': False,
                'error': 'Failed to process document',
                'original_filename': original_filename
            }), 500
    
    except Exception as e:
        logger.error(f"Error processing document {original_filename}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing document: {str(e)}',
            'original_filename': original_filename
        }), 500

@app.route('/documents', methods=['GET'])
def list_documents():
    """List uploaded and processed documents"""
    try:
        uploads_dir = 'data/uploads'
        processed_dir = 'data/processed'
        
        if not os.path.exists(uploads_dir) or not os.path.exists(processed_dir):
            return jsonify({
                'uploads': [],
                'processed': []
            }), 200
        
        # Get uploaded files with metadata
        uploads = []
        for filename in os.listdir(uploads_dir):
            if filename.endswith('.meta.json'):
                continue
                
            metadata_path = os.path.join(uploads_dir, filename + ".meta.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    uploads.append({
                        'filename': filename,
                        'original_filename': metadata.get('original_filename', filename),
                        'upload_time': metadata.get('upload_time', ''),
                        'source': metadata.get('source', 'unknown'),
                        'uploaded_by': metadata.get('uploaded_by', 'unknown')
                    })
            else:
                uploads.append({
                    'filename': filename,
                    'original_filename': filename,
                    'upload_time': '',
                    'source': 'unknown',
                    'uploaded_by': 'unknown'
                })
        
        # Get processed files
        processed = []
        for filename in os.listdir(processed_dir):
            if filename.endswith('.processed.txt'):
                metadata_path = os.path.join(processed_dir, filename + ".meta.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        processed.append({
                            'filename': filename,
                            'original_filename': metadata.get('original_filename', filename),
                            'processed_at': metadata.get('processed_at', ''),
                            'source': metadata.get('source', 'unknown'),
                            'indexed': 'indexed_at' in metadata
                        })
                else:
                    processed.append({
                        'filename': filename,
                        'original_filename': filename,
                        'processed_at': '',
                        'source': 'unknown',
                        'indexed': False
                    })
        
        return jsonify({
            'uploads': uploads,
            'processed': processed
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return jsonify({
            'error': f'Error listing documents: {str(e)}'
        }), 500

def start_api(host='0.0.0.0', port=5005):
    """Start the API server"""
    app.run(host=host, port=port)

if __name__ == '__main__':
    # Set up file logging
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(log_dir, 'upload_api.log'))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info("Starting Document Upload API")
    start_api(port=5005)
