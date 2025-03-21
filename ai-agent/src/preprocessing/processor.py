"""
Document Processor Module

This module handles preprocessing tax documents for RAG indexing.
It supports PDF text extraction, HTML cleaning, and document chunking.
"""

import os
import json
import logging
import PyPDF2
import glob
from datetime import datetime
import re

class DocumentProcessor:
    """Process downloaded tax documents for RAG indexing"""
    
    def __init__(self):
        """Initialize processor with directories"""
        self.download_dir = 'data/downloads'
        self.processed_dir = 'data/processed'
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('document_processor')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def process_new_files(self):
        """Process all new files in the download directory"""
        self.logger.info("Starting to process new downloaded files")
        
        # Get list of all files in download directory
        files = []
        for extension in ['pdf', 'txt', 'html', 'docx']:
            files.extend(glob.glob(os.path.join(self.download_dir, f'*.{extension}')))
        
        if not files:
            self.logger.info("No files found for processing")
            return []
        
        self.logger.info(f"Found {len(files)} files to process")
        processed_files = []
        
        for file_path in files:
            try:
                # Skip metadata files
                if file_path.endswith('.meta.json'):
                    continue
                
                # Skip already processed files
                processed_path = self._get_processed_path(file_path)
                if os.path.exists(processed_path):
                    self.logger.info(f"Skipping already processed file: {os.path.basename(file_path)}")
                    processed_files.append(processed_path)
                    continue
                
                # Process based on file type
                result = self.process_file(file_path)
                if result:
                    processed_files.append(result)
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {str(e)}")
        
        self.logger.info(f"Processed {len(processed_files)} files")
        return processed_files
    
    def process_file(self, file_path):
        """Process a single file based on its type"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        self.logger.info(f"Processing file: {os.path.basename(file_path)}")
        
        if file_ext == '.pdf':
            return self._process_pdf(file_path)
        elif file_ext == '.txt' or file_ext == '.html':
            return self._process_text(file_path)
        elif file_ext == '.docx':
            return self._process_docx(file_path)
        else:
            self.logger.warning(f"Unsupported file type: {file_ext}")
            return None
    
    def _process_pdf(self, file_path):
        """Extract text from PDF file"""
        try:
            output_path = self._get_processed_path(file_path)
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Extract text from each page
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"--- Page {i+1} ---\n{page_text}\n\n"
            
            # Clean up the text
            text = self._clean_text(text)
            
            # Save processed text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Copy and update metadata
            self._update_metadata(file_path, output_path)
            
            self.logger.info(f"Successfully processed PDF: {os.path.basename(file_path)}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return None
    
    def _process_text(self, file_path):
        """Process text or HTML files"""
        try:
            output_path = self._get_processed_path(file_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            
            # Clean up the text
            text = self._clean_text(text)
            
            # Save processed text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Copy and update metadata
            self._update_metadata(file_path, output_path)
            
            self.logger.info(f"Successfully processed text file: {os.path.basename(file_path)}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"Error processing text file {file_path}: {str(e)}")
            return None
    
    def _process_docx(self, file_path):
        """Process DOCX files"""
        try:
            # For DOCX processing, you would need python-docx package
            # This is a placeholder implementation
            self.logger.warning("DOCX processing not fully implemented yet")
            
            # For now, we'll just copy the metadata and return None
            output_path = self._get_processed_path(file_path)
            self._update_metadata(file_path, output_path)
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error processing DOCX {file_path}: {str(e)}")
            return None
    
    def _clean_text(self, text):
        """Clean and normalize text content"""
        # Replace multiple whitespaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove empty lines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _get_processed_path(self, file_path):
        """Generate the path for the processed file"""
        filename = os.path.basename(file_path)
        # Ensure the file has a .txt extension
        base_name = os.path.splitext(filename)[0]
        return os.path.join(self.processed_dir, f"{base_name}.processed.txt")
    
    def _update_metadata(self, original_path, processed_path):
        """Copy and update metadata for processed file"""
        meta_path = original_path + ".meta.json"
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            # Update metadata
            metadata["processed_at"] = datetime.now().isoformat()
            metadata["original_file"] = original_path
            metadata["processed_file"] = processed_path
            
            # Save updated metadata
            processed_meta_path = processed_path + ".meta.json"
            with open(processed_meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        else:
            self.logger.warning(f"No metadata found for {original_path}")

# Simple test to run if this module is run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    processor = DocumentProcessor()
    processor.process_new_files()
