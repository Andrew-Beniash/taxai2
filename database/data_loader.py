#!/usr/bin/env python3
"""
Tax Law Data Loader

This module loads tax law data into the SQLite database. It handles:
- Converting documents (PDFs, HTML, text) to structured database entries
- Adding metadata and tags to documents
- Managing document relationships and citations
- Integrating with the indexing system

Usage:
    python data_loader.py --source [path_to_documents] --db [database_file]
"""

import argparse
import sqlite3
import os
import json
import hashlib
import logging
from datetime import datetime
import re
from typing import Dict, List, Tuple, Any, Optional
import PyPDF2
from bs4 import BeautifulSoup
import requests
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_loader.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("data_loader")

# Database connection helper
def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Document extraction functions
def extract_text_from_pdf(pdf_path: str) -> Tuple[str, Dict[str, Any]]:
    """Extract text and metadata from a PDF file."""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            metadata = reader.metadata if reader.metadata else {}
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
                
            # Try to extract title if not in metadata
            if '/Title' not in metadata and text:
                # Simple heuristic: first line might be title
                potential_title = text.strip().split('\n')[0]
                if len(potential_title) < 100:  # Reasonable title length
                    metadata['/Title'] = potential_title
                    
            return text, {
                'title': metadata.get('/Title', os.path.basename(pdf_path)),
                'author': metadata.get('/Author', 'Unknown'),
                'creation_date': metadata.get('/CreationDate', ''),
                'page_count': len(reader.pages)
            }
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        return "", {'title': os.path.basename(pdf_path)}

def extract_text_from_html(html_path: str) -> Tuple[str, Dict[str, Any]]:
    """Extract text and metadata from an HTML file."""
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else os.path.basename(html_path)
        
        # Extract text from body
        text = soup.get_text(separator='\n')
        
        return text, {
            'title': title,
            'url': soup.find('link', {'rel': 'canonical'})['href'] if soup.find('link', {'rel': 'canonical'}) else '',
        }
    except Exception as e:
        logger.error(f"Error extracting text from HTML {html_path}: {str(e)}")
        return "", {'title': os.path.basename(html_path)}

def extract_text_from_url(url: str) -> Tuple[str, Dict[str, Any]]:
    """Extract text and metadata from a web URL."""
    try:
        response = requests.get(url, headers={'User-Agent': 'TaxLawBot/1.0'})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else url
        
        # Extract text from body
        text = soup.get_text(separator='\n')
        
        return text, {
            'title': title,
            'url': url,
            'date_accessed': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error extracting text from URL {url}: {str(e)}")
        return "", {'title': url}

def extract_text_from_txt(txt_path: str) -> Tuple[str, Dict[str, Any]]:
    """Extract text from a plain text file."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text, {'title': os.path.basename(txt_path)}
    except Exception as e:
        logger.error(f"Error extracting text from text file {txt_path}: {str(e)}")
        return "", {'title': os.path.basename(txt_path)}

def detect_document_type(text: str, metadata: Dict[str, Any]) -> str:
    """Determine the type of tax document based on content analysis."""
    text_lower = text.lower()
    
    # Check for court cases
    if re.search(r'\bv\.\s+commissioner\b', text_lower) or \
       re.search(r'tax\s+court', text_lower) or \
       re.search(r'court\s+of\s+appeals', text_lower):
        return "court_case"
    
    # Check for IRS publications
    if re.search(r'publication\s+\d+', text_lower) or \
       re.search(r'internal\s+revenue\s+service', text_lower) or \
       re.search(r'department\s+of\s+treasury', text_lower):
        return "publication"
    
    # Check for regulations
    if re.search(r'regulation\s+section', text_lower) or \
       re.search(r'treas\.\s+reg', text_lower) or \
       re.search(r'code\s+section', text_lower):
        return "regulation"
    
    # Check for revenue rulings
    if re.search(r'rev\.\s+rul\.', text_lower) or \
       re.search(r'revenue\s+ruling', text_lower):
        return "revenue_ruling"
    
    # Default to generic document
    return "general"

def extract_sections(text: str) -> List[Dict[str, str]]:
    """Extract logical sections from a document."""
    # Simple regex-based section extraction
    # This is a basic implementation and can be enhanced with more sophisticated parsing
    section_pattern = re.compile(r'(^|\n)(\d+\.\d+(?:\.\d+)*)\s+(.*?)(?=\n\d+\.\d+(?:\.\d+)*\s+|\Z)', re.DOTALL)
    
    sections = []
    for match in section_pattern.finditer(text):
        section_number = match.group(2)
        title_and_content = match.group(3).strip()
        
        # Try to separate title from content
        lines = title_and_content.split('\n', 1)
        if len(lines) > 1:
            title, content = lines
            sections.append({
                'section_number': section_number,
                'section_title': title.strip(),
                'content': content.strip()
            })
        else:
            sections.append({
                'section_number': section_number,
                'section_title': '',
                'content': title_and_content
            })
    
    # If no sections found with pattern, create a single section
    if not sections:
        sections.append({
            'section_number': '1',
            'section_title': '',
            'content': text
        })
        
    return sections

def extract_potential_tags(text: str) -> List[str]:
    """Extract potential tags from document text based on keywords."""
    tax_terms = {
        'income tax': ['income tax', 'individual income', 'taxable income'],
        'corporate tax': ['corporate tax', 'corporation tax', 'business entity'],
        'tax deduction': ['deduction', 'deductions', 'deductible'],
        'tax credit': ['tax credit', 'credits', 'creditable'],
        'capital gains': ['capital gain', 'capital gains', 'capital loss'],
        'estate tax': ['estate tax', 'estate planning', 'inheritance'],
        'gift tax': ['gift tax', 'gifts', 'gifting'],
        'sales tax': ['sales tax', 'use tax', 'transaction tax'],
        'property tax': ['property tax', 'real estate tax', 'assessment'],
        'international tax': ['international tax', 'foreign tax', 'global tax'],
        # Add more categories as needed
    }
    
    found_tags = set()
    text_lower = text.lower()
    
    for tag, keywords in tax_terms.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_tags.add(tag)
                break
    
    return list(found_tags)

def detect_citations(text: str) -> List[Dict[str, str]]:
    """Detect citations to other tax documents."""
    citation_patterns = [
        # IRS Publications
        (r'Publication\s+(\d+)', 'publication'),
        # Code sections
        (r'(?:IRC|I\.R\.C\.|Code)\s+[§]?\s*(\d+[A-Za-z]?(?:\([a-zA-Z0-9]+\))*)', 'code_section'),
        # Regulations
        (r'(?:Treas\.|Treasury)\s+Reg\.\s+[§]?\s*(\d+\.\d+(?:-\d+)*)', 'regulation'),
        # Revenue Rulings
        (r'Rev\.\s+Rul\.\s+(\d+-\d+)', 'revenue_ruling'),
        # Court Cases
        (r'([A-Za-z\s\.]+)\s+v\.\s+([A-Za-z\s\.]+),\s+(\d+\s+[A-Za-z\.]+\s+\d+)', 'court_case')
    ]
    
    citations = []
    
    for pattern, doc_type in citation_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            citation_text = match.group(0)
            citation_id = match.group(1)
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            
            citations.append({
                'citation_text': citation_text,
                'citation_id': citation_id,
                'doc_type': doc_type,
                'context': context
            })
    
    return citations

class TaxDataLoader:
    """Main class for loading tax documents into the database."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = db_path
        # Ensure database is initialized
        conn = get_db_connection(db_path)
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()
        
    def load_document(self, file_path: str, source: str) -> Optional[int]:
        """Load a document into the database from a file."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Extract text and metadata based on file type
        if file_ext == '.pdf':
            text, metadata = extract_text_from_pdf(file_path)
        elif file_ext in ['.html', '.htm']:
            text, metadata = extract_text_from_html(file_path)
        elif file_ext == '.txt':
            text, metadata = extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_ext} for {file_path}")
            return None
        
        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return None
        
        # Determine document type
        doc_type = detect_document_type(text, metadata)
        
        # Extract sections, tags, and citations
        sections = extract_sections(text)
        tags = extract_potential_tags(text)
        citations = detect_citations(text)
        
        # Save to database
        return self._save_document_to_db(
            title=metadata.get('title', os.path.basename(file_path)),
            source=source,
            source_url=metadata.get('url', ''),
            document_type=doc_type,
            content=text,
            sections=sections,
            tags=tags,
            citations=citations
        )
    
    def load_from_url(self, url: str, source: str) -> Optional[int]:
        """Load a document into the database from a URL."""
        text, metadata = extract_text_from_url(url)
        
        if not text:
            logger.warning(f"No text extracted from URL: {url}")
            return None
        
        # Determine document type
        doc_type = detect_document_type(text, metadata)
        
        # Extract sections, tags, and citations
        sections = extract_sections(text)
        tags = extract_potential_tags(text)
        citations = detect_citations(text)
        
        # Save to database
        return self._save_document_to_db(
            title=metadata.get('title', url),
            source=source,
            source_url=url,
            document_type=doc_type,
            content=text,
            sections=sections,
            tags=tags,
            citations=citations
        )
    
    def _save_document_to_db(
        self, 
        title: str, 
        source: str, 
        source_url: str,
        document_type: str, 
        content: str,
        sections: List[Dict[str, str]],
        tags: List[str],
        citations: List[Dict[str, str]]
    ) -> Optional[int]:
        """Save a document and its related data to the database."""
        conn = get_db_connection(self.db_path)
        doc_id = None
        
        try:
            conn.execute('BEGIN TRANSACTION')
            
            # Insert main document
            cursor = conn.execute(
                '''INSERT INTO tax_documents 
                   (title, source, source_url, document_type, content, date_indexed, is_active) 
                   VALUES (?, ?, ?, ?, ?, ?, 1)''',
                (title, source, source_url, document_type, content, datetime.now().isoformat())
            )
            doc_id = cursor.lastrowid
            
            # Insert sections
            for section in sections:
                conn.execute(
                    '''INSERT INTO document_sections
                       (document_id, section_number, section_title, content)
                       VALUES (?, ?, ?, ?)''',
                    (doc_id, section.get('section_number', ''), 
                     section.get('section_title', ''), section.get('content', ''))
                )
            
            # Insert tags
            for tag_name in tags:
                # Insert tag if not exists
                conn.execute(
                    'INSERT OR IGNORE INTO tags (tag_name) VALUES (?)',
                    (tag_name,)
                )
                
                # Get tag ID
                cursor = conn.execute('SELECT id FROM tags WHERE tag_name = ?', (tag_name,))
                tag_id = cursor.fetchone()[0]
                
                # Link tag to document
                conn.execute(
                    'INSERT INTO document_tags (document_id, tag_id) VALUES (?, ?)',
                    (doc_id, tag_id)
                )
            
            # Note: Citations would require matching with existing documents
            # This would be implemented in a separate process once we have documents loaded
            
            conn.commit()
            logger.info(f"Successfully loaded document: {title} (ID: {doc_id})")
            return doc_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving document {title}: {str(e)}")
            return None
        finally:
            conn.close()
    
    def load_directory(self, directory_path: str, source: str) -> List[int]:
        """Load all documents from a directory."""
        doc_ids = []
        
        if not os.path.exists(directory_path):
            logger.error(f"Directory does not exist: {directory_path}")
            return doc_ids
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in ['.pdf', '.html', '.htm', '.txt']:
                    doc_id = self.load_document(file_path, source)
                    if doc_id:
                        doc_ids.append(doc_id)
        
        return doc_ids
    
    def get_document_count(self) -> int:
        """Get the total number of documents in the database."""
        conn = get_db_connection(self.db_path)
        count = conn.execute('SELECT COUNT(*) FROM tax_documents').fetchone()[0]
        conn.close()
        return count

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Load tax law documents into the database.')
    parser.add_argument('--source', required=True, help='Path to documents or URL')
    parser.add_argument('--db', default='tax_law.db', help='Database file path')
    parser.add_argument('--type', default='file', choices=['file', 'directory', 'url'],
                        help='Type of source to load')
    parser.add_argument('--source-name', default='Manual Import',
                        help='Name of the source (e.g., "IRS Website", "Tax Court Database")')
    
    args = parser.parse_args()
    
    loader = TaxDataLoader(args.db)
    
    if args.type == 'file':
        doc_id = loader.load_document(args.source, args.source_name)
        if doc_id:
            print(f"Successfully loaded document with ID: {doc_id}")
        else:
            print("Failed to load document")
            
    elif args.type == 'directory':
        doc_ids = loader.load_directory(args.source, args.source_name)
        print(f"Loaded {len(doc_ids)} documents from directory")
        
    elif args.type == 'url':
        doc_id = loader.load_from_url(args.source, args.source_name)
        if doc_id:
            print(f"Successfully loaded document from URL with ID: {doc_id}")
        else:
            print("Failed to load document from URL")
    
    total_docs = loader.get_document_count()
    print(f"Total documents in database: {total_docs}")

if __name__ == '__main__':
    main()
