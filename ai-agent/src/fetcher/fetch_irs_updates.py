"""
This module fetches the latest tax regulations from IRS.gov and other tax-related sources.
It monitors various IRS web pages for updates and downloads new documents for processing.
"""

import os
import re
import time
import logging
import hashlib
import json
import urllib.parse
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import configuration
from src.config import (
    IRS_NEWSROOM_URL, IRS_TAX_FORMS_URL, IRS_PUBLICATIONS_URL, 
    IRS_TAX_TOPICS_URL, US_TAX_COURT_URL, PDF_STORAGE_DIR, 
    METADATA_DIR, MAX_RETRIES, REQUEST_TIMEOUT
)

logger = logging.getLogger('ai_tax_agent.fetcher')


class IRSUpdateFetcher:
    """Class to fetch and monitor tax law updates from various sources."""
    
    def __init__(self):
        """Initialize the fetcher with required settings."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Tax Law Assistant Bot/1.0 (Educational Research)',
            'Accept': 'text/html,application/xhtml+xml,application/xml,application/pdf'
        })
        
        # Create metadata directory if it doesn't exist
        os.makedirs(METADATA_DIR, exist_ok=True)
        self.last_fetch_file = os.path.join(METADATA_DIR, 'last_fetch.json')
        
        # Load last fetch data
        self.last_fetch_data = self._load_last_fetch_data()
    
    def _load_last_fetch_data(self):
        """Load data about the last fetch operation from disk."""
        if os.path.exists(self.last_fetch_file):
            try:
                with open(self.last_fetch_file, 'r') as file:
                    return json.load(file)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading last fetch data: {e}")
        
        # Return default data if file doesn't exist or has errors
        return {
            'newsroom': {'last_fetch': None, 'last_urls': []},
            'tax_forms': {'last_fetch': None, 'last_urls': []},
            'publications': {'last_fetch': None, 'last_urls': []},
            'tax_topics': {'last_fetch': None, 'last_urls': []},
            'tax_court': {'last_fetch': None, 'last_urls': []}
        }
    
    def _save_last_fetch_data(self):
        """Save data about the current fetch operation to disk."""
        try:
            with open(self.last_fetch_file, 'w') as file:
                json.dump(self.last_fetch_data, file, indent=2)
        except IOError as e:
            logger.error(f"Error saving last fetch data: {e}")
    
    def _make_request(self, url, retries=MAX_RETRIES):
        """Make an HTTP request with retries on failure."""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{retries}): {url}, Error: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _is_new_url(self, url, source_key):
        """Check if a URL is new and hasn't been processed before."""
        return url not in self.last_fetch_data[source_key]['last_urls']
    
    def _download_pdf(self, url, filename=None):
        """Download a PDF file and save it to disk."""
        try:
            response = self._make_request(url)
            
            # Generate filename if not provided
            if filename is None:
                # Extract filename from URL or content disposition header
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition and 'filename=' in content_disposition:
                    filename = re.findall('filename=(.+)', content_disposition)[0].strip('"\'')
                else:
                    # Use the last part of the URL or hash if not available
                    url_path = urllib.parse.urlparse(url).path
                    filename = os.path.basename(url_path)
                    if not filename or len(filename) < 5:
                        filename = f"{hashlib.md5(url.encode()).hexdigest()}.pdf"
            
            # Ensure filename has .pdf extension
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            # Create full path
            filepath = os.path.join(PDF_STORAGE_DIR, filename)
            
            # Save the PDF
            with open(filepath, 'wb') as file:
                file.write(response.content)
            
            logger.info(f"Downloaded PDF: {filename} from {url}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}")
            return None
    
    def _parse_date(self, date_str):
        """Parse various date formats into a datetime object."""
        try:
            # Try various date formats
            for date_format in ["%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%Y-%m-%d"]:
                try:
                    return datetime.strptime(date_str.strip(), date_format)
                except ValueError:
                    continue
            
            # If we can't parse the date, log a warning and return current date
            logger.warning(f"Could not parse date string: {date_str}")
            return datetime.now()
        
        except Exception as e:
            logger.error(f"Error parsing date: {e}")
            return datetime.now()
    
    def fetch_irs_newsroom(self):
        """Fetch updates from the IRS Newsroom."""
        logger.info(f"Fetching updates from IRS Newsroom: {IRS_NEWSROOM_URL}")
        
        try:
            response = self._make_request(IRS_NEWSROOM_URL)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find all news items
            news_items = []
            articles = soup.find_all("div", class_="newsroom-article-item")
            
            # Process each article
            for article in articles:
                try:
                    # Extract article details
                    title_elem = article.find("h4")
                    title = title_elem.text.strip() if title_elem else "No title"
                    
                    link_elem = title_elem.find("a") if title_elem else None
                    link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else None
                    
                    # Make sure link is absolute
                    if link and not link.startswith('http'):
                        link = urllib.parse.urljoin(IRS_NEWSROOM_URL, link)
                    
                    # Extract date
                    date_elem = article.find("time")
                    date_str = date_elem.text.strip() if date_elem else None
                    date = self._parse_date(date_str) if date_str else datetime.now()
                    
                    # Only process new articles
                    if link and self._is_new_url(link, 'newsroom'):
                        news_items.append({
                            'title': title,
                            'link': link,
                            'date': date.strftime("%Y-%m-%d"),
                            'source': 'IRS Newsroom'
                        })
                except Exception as e:
                    logger.error(f"Error processing newsroom article: {e}")
            
            # Update last fetch data
            current_urls = [item['link'] for item in news_items]
            self.last_fetch_data['newsroom']['last_urls'] = current_urls
            self.last_fetch_data['newsroom']['last_fetch'] = datetime.now().isoformat()
            self._save_last_fetch_data()
            
            logger.info(f"Found {len(news_items)} new items in IRS Newsroom")
            return news_items
        
        except Exception as e:
            logger.error(f"Error fetching IRS Newsroom: {e}")
            return []
    
    def fetch_tax_court_opinions(self):
        """Fetch recent opinions from the US Tax Court."""
        logger.info(f"Fetching opinions from US Tax Court: {US_TAX_COURT_URL}")
        
        try:
            response = self._make_request(US_TAX_COURT_URL)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find all opinion items
            opinions = []
            opinion_elements = soup.find_all("tr", class_="opinionsItem")
            
            # Process each opinion
            for opinion in opinion_elements:
                try:
                    # Extract opinion details
                    cells = opinion.find_all("td")
                    if len(cells) >= 3:
                        date_str = cells[0].text.strip()
                        name = cells[1].text.strip()
                        
                        link_elem = cells[2].find("a")
                        link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else None
                        
                        # Make sure link is absolute
                        if link and not link.startswith('http'):
                            link = urllib.parse.urljoin(US_TAX_COURT_URL, link)
                        
                        # Only process new opinions
                        if link and self._is_new_url(link, 'tax_court'):
                            date = self._parse_date(date_str)
                            opinions.append({
                                'title': name,
                                'link': link,
                                'date': date.strftime("%Y-%m-%d"),
                                'source': 'US Tax Court'
                            })
                except Exception as e:
                    logger.error(f"Error processing tax court opinion: {e}")
            
            # Update last fetch data
            current_urls = [item['link'] for item in opinions]
            self.last_fetch_data['tax_court']['last_urls'] = current_urls
            self.last_fetch_data['tax_court']['last_fetch'] = datetime.now().isoformat()
            self._save_last_fetch_data()
            
            logger.info(f"Found {len(opinions)} new opinions in US Tax Court")
            return opinions
        
        except Exception as e:
            logger.error(f"Error fetching US Tax Court opinions: {e}")
            return []
    
    def fetch_irs_publications(self):
        """Fetch IRS publications and forms."""
        logger.info(f"Fetching publications from IRS: {IRS_PUBLICATIONS_URL}")
        
        try:
            response = self._make_request(IRS_PUBLICATIONS_URL)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find all publication items
            publications = []
            pub_elements = soup.find_all("div", class_="field-item")
            
            # Process each publication
            for pub in pub_elements:
                try:
                    # Extract publication details
                    link_elem = pub.find("a")
                    if not link_elem or 'href' not in link_elem.attrs:
                        continue
                    
                    link = link_elem['href']
                    title = link_elem.text.strip()
                    
                    # Make sure link is absolute
                    if not link.startswith('http'):
                        link = urllib.parse.urljoin(IRS_PUBLICATIONS_URL, link)
                    
                    # Only process PDF links that are new
                    if link.endswith('.pdf') and self._is_new_url(link, 'publications'):
                        publications.append({
                            'title': title,
                            'link': link,
                            'date': datetime.now().strftime("%Y-%m-%d"),  # Use current date as fallback
                            'source': 'IRS Publications'
                        })
                except Exception as e:
                    logger.error(f"Error processing IRS publication: {e}")
            
            # Update last fetch data
            current_urls = [item['link'] for item in publications]
            self.last_fetch_data['publications']['last_urls'] = current_urls
            self.last_fetch_data['publications']['last_fetch'] = datetime.now().isoformat()
            self._save_last_fetch_data()
            
            logger.info(f"Found {len(publications)} new IRS publications")
            return publications
        
        except Exception as e:
            logger.error(f"Error fetching IRS publications: {e}")
            return []
    
    def download_documents(self, documents):
        """Download documents (PDFs) from the provided list."""
        downloaded = []
        
        for doc in documents:
            try:
                if 'link' in doc and doc['link'].endswith('.pdf'):
                    # Generate a filename from the document title
                    safe_title = re.sub(r'[^\w\-.]', '_', doc['title'])
                    filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    
                    # Download the PDF
                    pdf_path = self._download_pdf(doc['link'], filename)
                    
                    if pdf_path:
                        # Store metadata about the downloaded document
                        metadata = doc.copy()
                        metadata['local_path'] = pdf_path
                        metadata['download_date'] = datetime.now().isoformat()
                        downloaded.append(metadata)
            except Exception as e:
                logger.error(f"Error downloading document {doc.get('title', 'Unknown')}: {e}")
        
        logger.info(f"Downloaded {len(downloaded)} documents")
        return downloaded
    
    def fetch_all_updates(self):
        """Fetch updates from all sources and download new documents."""
        all_updates = []
        
        # Fetch from various sources
        all_updates.extend(self.fetch_irs_newsroom())
        all_updates.extend(self.fetch_tax_court_opinions())
        all_updates.extend(self.fetch_irs_publications())
        
        # Download new documents
        downloaded_docs = self.download_documents(all_updates)
        
        return downloaded_docs


if __name__ == "__main__":
    # Setup basic logging for standalone testing
    logging.basicConfig(level=logging.INFO)
    
    # Create and test the fetcher
    fetcher = IRSUpdateFetcher()
    updates = fetcher.fetch_all_updates()
    
    print(f"Found {len(updates)} new tax law updates")
    for update in updates[:5]:  # Print first 5 updates
        print(f"- {update['title']} ({update['source']}, {update['date']})")
