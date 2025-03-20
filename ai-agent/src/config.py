"""
Configuration settings for the AI-powered Tax Law Fetcher.
This module contains configuration parameters, URLs, and settings
for the agent's operation.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys and credentials (set these in .env file)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Data storage paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PDF_STORAGE_DIR = os.path.join(DATA_DIR, 'pdfs')
TEXT_STORAGE_DIR = os.path.join(DATA_DIR, 'texts')
METADATA_DIR = os.path.join(DATA_DIR, 'metadata')
DB_PATH = os.path.join(DATA_DIR, 'tax_documents.db')

# Create directories if they don't exist
for directory in [DATA_DIR, PDF_STORAGE_DIR, TEXT_STORAGE_DIR, METADATA_DIR]:
    os.makedirs(directory, exist_ok=True)

# URLs for data sources
IRS_NEWSROOM_URL = "https://www.irs.gov/newsroom"
IRS_TAX_FORMS_URL = "https://www.irs.gov/forms-instructions"
IRS_PUBLICATIONS_URL = "https://www.irs.gov/publications"
IRS_TAX_TOPICS_URL = "https://www.irs.gov/taxtopics"
US_TAX_COURT_URL = "https://www.ustaxcourt.gov/opinions.html"

# Schedule settings
FETCH_INTERVAL_HOURS = 24  # Fetch new data every 24 hours
CLEANUP_INTERVAL_DAYS = 30  # Clean outdated data every 30 days

# Processing settings
MAX_RETRIES = 3  # Maximum number of retries for failed requests
REQUEST_TIMEOUT = 60  # Timeout for HTTP requests in seconds
BATCH_SIZE = 10  # Number of documents to process in a batch
MAX_PDF_SIZE_MB = 50  # Maximum PDF file size to download (in MB)

# Database settings
DB_CONNECT_STRING = f"sqlite:///{DB_PATH}"
