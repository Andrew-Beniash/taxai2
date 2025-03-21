"""
Document Fetcher Module

This module handles downloading tax documents from various sources based on configuration.
It supports PDF downloads, HTML scraping, and recursive link following.
"""

import json
import requests
import os
from bs4 import BeautifulSoup
import logging
import urllib.parse
import time
from datetime import datetime

class DocumentFetcher:
    """Fetch tax documents from configured sources"""
    
    def __init__(self, config_path='src/config/sources.json'):
        """Initialize with config path"""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Set up download directory
        self.download_dir = 'data/downloads'
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('document_fetcher')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def fetch_all_documents(self):
        """Fetch all documents defined in the configuration"""
        self.logger.info("Starting to fetch all configured documents")
        
        for doc in self.config['documents']:
            try:
                self.logger.info(f"Fetching document: {doc['description']} from {doc['url']}")
                self.fetch_document(doc)
            except Exception as e:
                self.logger.error(f"Error fetching document {doc['url']}: {str(e)}")
        
        self.logger.info("Completed fetching all documents")
        return True
    
    def fetch_document(self, doc_config):
        """Fetch a specific document based on its configuration"""
        url = doc_config['url']
        doc_type = doc_config['type']
        source = doc_config['source']
        
        self.logger.info(f"Processing {doc_type} from {url}")
        
        if doc_type == 'pdf':
            self._download_pdf(url, source)
        elif doc_type == 'html':
            if doc_config.get('recursive', False):
                self._scrape_links(url, source)
            else:
                self._download_html(url, source)
        else:
            self.logger.warning(f"Unsupported document type: {doc_type}")
        
        self.logger.info(f"Successfully processed {url}")
    
    def _download_pdf(self, url, source):
        """Download a PDF file"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raise an error for bad responses
            
            filename = url.split('/')[-1]
            filepath = os.path.join(self.download_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Downloaded PDF: {filename}")
            
            # Save metadata
            metadata_path = filepath + ".meta.json"
            metadata = {
                "source": source,
                "url": url,
                "downloaded_at": datetime.now().isoformat(),
                "file_type": "pdf"
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return filepath
        
        except Exception as e:
            self.logger.error(f"Error downloading PDF {url}: {str(e)}")
            return None
    
    def _download_html(self, url, source):
        """Download HTML content"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Generate filename from URL
            parsed_url = urllib.parse.urlparse(url)
            path = parsed_url.path
            if path.endswith('/'):
                path = path[:-1]
            
            if not path:
                filename = parsed_url.netloc.replace('.', '_') + '.txt'
            else:
                filename = os.path.basename(path)
                if not filename:
                    filename = path.replace('/', '_').strip('_')
                if not filename.endswith('.txt'):
                    filename += '.txt'
            
            filepath = os.path.join(self.download_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            self.logger.info(f"Downloaded HTML content: {filename}")
            
            # Save metadata
            metadata_path = filepath + ".meta.json"
            metadata = {
                "source": source,
                "url": url,
                "downloaded_at": datetime.now().isoformat(),
                "file_type": "html"
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return filepath
        
        except Exception as e:
            self.logger.error(f"Error downloading HTML {url}: {str(e)}")
            return None
    
    def _scrape_links(self, base_url, source):
        """Recursively scrape links from a webpage"""
        try:
            self.logger.info(f"Scraping links from {base_url}")
            
            response = requests.get(base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            
            # Keep track of downloaded files to avoid duplicates
            downloaded_count = 0
            
            for link in links:
                href = link.get('href')
                if not href:
                    continue
                
                # Filter for document types we want
                allowed_extensions = self.config['fileTypes']
                
                # Check if href ends with any of the allowed extensions
                is_allowed = any(href.lower().endswith('.' + ext.lower()) for ext in allowed_extensions)
                
                if is_allowed:
                    # Make relative URLs absolute
                    full_url = urllib.parse.urljoin(base_url, href)
                    
                    # Download the file
                    self._download_file(full_url, source)
                    downloaded_count += 1
                    
                    # Be nice to the server
                    time.sleep(1)
            
            self.logger.info(f"Scraped and downloaded {downloaded_count} files from {base_url}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error scraping links from {base_url}: {str(e)}")
            return False
    
    def _download_file(self, url, source):
        """Download any file type"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract filename from URL
            filename = url.split('/')[-1]
            if not filename:
                filename = 'unnamed_file_' + str(int(time.time()))
            
            filepath = os.path.join(self.download_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Downloaded file: {filename}")
            
            # Save metadata
            metadata_path = filepath + ".meta.json"
            metadata = {
                "source": source,
                "url": url,
                "downloaded_at": datetime.now().isoformat(),
                "file_type": os.path.splitext(filename)[1][1:] if '.' in filename else "unknown"
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return filepath
        
        except Exception as e:
            self.logger.error(f"Error downloading file {url}: {str(e)}")
            return None

# Simple test to run if this module is run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = DocumentFetcher()
    fetcher.fetch_all_documents()
