#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the AI-powered Tax Law Fetcher agent.
This script initializes the agent and starts the scheduler that will
periodically fetch and process tax law updates.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agent components
from src.fetcher.fetch_irs_updates import IRSUpdateFetcher
from src.preprocessing.preprocess_documents import DocumentProcessor
from src.scheduler.scheduler import TaxLawUpdateScheduler


def setup_logging():
    """Configure logging for the application."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("ai_agent.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('ai_tax_agent')


def main():
    """Initialize and run the Tax Law Fetcher agent."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting AI Tax Law Fetcher Agent")
    
    # Initialize components
    irs_fetcher = IRSUpdateFetcher()
    document_processor = DocumentProcessor()
    
    # Create and start the scheduler
    scheduler = TaxLawUpdateScheduler(
        fetcher=irs_fetcher,
        processor=document_processor
    )
    
    try:
        # Start the scheduler for periodic updates
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down AI Tax Law Fetcher Agent")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Error in AI Tax Law Fetcher Agent: {e}")
        scheduler.shutdown()
        raise


if __name__ == "__main__":
    main()
