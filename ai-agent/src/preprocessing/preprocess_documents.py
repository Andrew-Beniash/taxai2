"""
This module handles the preprocessing of tax documents, including:
- Text extraction from PDFs
- Cleaning and formatting text content
- Storing documents in a structured format
- Indexing document content for later retrieval
"""

import os
import re
import json
import logging
import hashlib
import sqlite3
from datetime import datetime
import PyPDF2
from io import StringIO
import sys
from tqdm import tqdm
import nltk

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import configuration
from src.config import (
    PDF_STORAGE_DIR, TEXT_STORAGE_DIR, METADATA_DIR, 
    DB_PATH, BATCH_SIZE
)

# Initialize logger
logger = logging.getLogger('ai_tax_agent.preprocessor')

# Download required NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK resources: {e}")


class DocumentProcessor:
    """Class to process and store tax law documents."""
    
    def __init__(self):
        """Initialize the document processor."""
        # Create necessary directories if they don't exist
        for directory in [TEXT_STORAGE_DIR, METADATA_DIR]:
            os.makedirs(directory, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database for document storage."""
        try:
            # Create database directory if it doesn't exist
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            
            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    source TEXT,
                    document_date TEXT,
                    download_date TEXT,
                    pdf_path TEXT,
                    text_path TEXT,
                    word_count INTEGER,
                    hash TEXT UNIQUE,
                    metadata TEXT
                )
            ''')
            
            # Create index on hash for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_hash ON documents(hash)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _extract_text_from_pdf(self, pdf_path):
        """Extract text content from a PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                # Create PDF reader
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    try:
                        # Try to decrypt with empty password
                        pdf_reader.decrypt('')
                    except Exception:
                        logger.warning(f"Could not decrypt PDF: {pdf_path}")
                        return None
                
                # Extract text from each page
                text_content = StringIO()
                for page_num in range(len(pdf_reader.pages)):
                    try:
                        page = pdf_reader.pages[page_num]
                        text_content.write(page.extract_text())
                        text_content.write("\n\n")  # Add page break
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num} in {pdf_path}: {e}")
                
                return text_content.getvalue()
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return None
    
    def _clean_text(self, text):
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Replace multiple spaces and newlines with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x09\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Split text into sentences for better processing
        try:
            sentences = nltk.sent_tokenize(text)
            cleaned_text = ' '.join(sentences)
        except Exception:
            cleaned_text = text
        
        return cleaned_text.strip()
    
    def _compute_document_hash(self, content):
        """Compute a hash of the document content for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _document_exists(self, doc_hash):
        """Check if a document with the given hash already exists in the database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM documents WHERE hash = ?", (doc_hash,))
            result = cursor.fetchone() is not None
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return False
    
    def _store_text(self, text, title, doc_date):
        """Store the extracted text as a file."""
        try:
            # Create a safe filename from the title
            safe_title = re.sub(r'[^\w\-.]', '_', title)
            filename = f"{safe_title}_{doc_date}.txt"
            filepath = os.path.join(TEXT_STORAGE_DIR, filename)
            
            # Write text to file
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(text)
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error storing text for {title}: {e}")
            return None
    
    def _store_document_metadata(self, document, text_path):
        """Store document metadata in the database."""
        try:
            # Prepare metadata
            metadata = {
                'title': document.get('title', 'Untitled'),
                'source': document.get('source', 'Unknown'),
                'document_date': document.get('date', datetime.now().strftime("%Y-%m-%d")),
                'download_date': document.get('download_date', datetime.now().isoformat()),
                'pdf_path': document.get('local_path', ''),
                'text_path': text_path,
                'word_count': len(document.get('text', '').split()),
                'hash': document.get('hash', ''),
                'metadata': json.dumps({
                    'link': document.get('link', ''),
                    'additional_info': document.get('additional_info', {})
                })
            }
            
            # Insert into database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents 
                (title, source, document_date, download_date, pdf_path, text_path, word_count, hash, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata['title'], metadata['source'], metadata['document_date'],
                metadata['download_date'], metadata['pdf_path'], metadata['text_path'],
                metadata['word_count'], metadata['hash'], metadata['metadata']
            ))
            conn.commit()
            conn.close()
            
            logger.info(f"Stored metadata for document: {metadata['title']}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing document metadata: {e}")
            return False
    
    def process_document(self, document):
        """Process a single document from download to storage."""
        try:
            # Extract PDF path from document metadata
            pdf_path = document.get('local_path')
            if not pdf_path or not os.path.exists(pdf_path):
                logger.warning(f"PDF file not found: {pdf_path}")
                return False
            
            # Extract text from PDF
            text = self._extract_text_from_pdf(pdf_path)
            if not text:
                logger.warning(f"Could not extract text from PDF: {pdf_path}")
                return False
            
            # Clean the extracted text
            cleaned_text = self._clean_text(text)
            if not cleaned_text:
                logger.warning(f"Text cleaning resulted in empty content: {pdf_path}")
                return False
            
            # Compute document hash for deduplication
            doc_hash = self._compute_document_hash(cleaned_text)
            
            # Check if document already exists
            if self._document_exists(doc_hash):
                logger.info(f"Document already exists: {document.get('title')}")
                return False
            
            # Store the cleaned text
            doc_date = document.get('date', datetime.now().strftime("%Y%m%d"))
            text_path = self._store_text(cleaned_text, document.get('title', 'Untitled'), doc_date)
            
            if not text_path:
                logger.warning(f"Failed to store text for {document.get('title')}")
                return False
            
            # Add text and hash to document metadata
            document['text'] = cleaned_text
            document['hash'] = doc_hash
            
            # Store document metadata
            success = self._store_document_metadata(document, text_path)
            
            return success
        
        except Exception as e:
            logger.error(f"Error processing document {document.get('title', 'Unknown')}: {e}")
            return False
    
    def process_documents(self, documents):
        """Process a batch of documents."""
        processed_count = 0
        
        logger.info(f"Processing {len(documents)} documents")
        
        # Process documents in batches
        for i in range(0, len(documents), BATCH_SIZE):
            batch = documents[i:i+BATCH_SIZE]
            
            for doc in tqdm(batch, desc=f"Processing batch {i//BATCH_SIZE + 1}"):
                if self.process_document(doc):
                    processed_count += 1
        
        logger.info(f"Successfully processed {processed_count} out of {len(documents)} documents")
        return processed_count
    
    def clean_outdated_documents(self, days_threshold=90):
        """Remove outdated documents from the database."""
        try:
            # Calculate the cutoff date
            cutoff_date = (datetime.now() - datetime.timedelta(days=days_threshold)).strftime("%Y-%m-%d")
            
            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Find outdated documents
            cursor.execute("""
                SELECT id, pdf_path, text_path FROM documents 
                WHERE document_date < ?
            """, (cutoff_date,))
            
            outdated_docs = cursor.fetchall()
            
            for doc_id, pdf_path, text_path in outdated_docs:
                # Remove PDF file if it exists
                if pdf_path and os.path.exists(pdf_path):
                    os.remove(pdf_path)
                
                # Remove text file if it exists
                if text_path and os.path.exists(text_path):
                    os.remove(text_path)
                
                # Remove from database
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned {len(outdated_docs)} outdated documents")
            return len(outdated_docs)
        
        except Exception as e:
            logger.error(f"Error cleaning outdated documents: {e}")
            return 0


if __name__ == "__main__":
    # Setup basic logging for standalone testing
    logging.basicConfig(level=logging.INFO)
    
    # Create processor and process a test document
    processor = DocumentProcessor()
    
    # Test with a sample PDF if one exists
    test_pdfs = [f for f in os.listdir(PDF_STORAGE_DIR) if f.endswith('.pdf')]
    
    if test_pdfs:
        test_pdf = test_pdfs[0]
        test_doc = {
            'title': 'Test Document',
            'source': 'Test',
            'date': datetime.now().strftime("%Y-%m-%d"),
            'local_path': os.path.join(PDF_STORAGE_DIR, test_pdf)
        }
        
        result = processor.process_document(test_doc)
        print(f"Test document processing {'successful' if result else 'failed'}")
    else:
        print("No test PDFs found in storage directory")
