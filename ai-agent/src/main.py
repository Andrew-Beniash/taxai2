"""
Main Entry Point for Tax Law AI Agent

This script is the main entry point for the autonomous AI agent
that maintains the RAG database with tax law information.
"""

import logging
import argparse
import os
import sys
import threading
import time
from datetime import datetime

# Import our components
from src.scheduler.scheduler import DocumentScheduler
from src.fetcher.document_fetcher import DocumentFetcher
from src.preprocessing.processor import DocumentProcessor
from src.indexing.indexer import DocumentIndexer
from src.monitoring.health_check import HealthMonitor
from src.api.upload_api import start_api

def setup_logging():
    """Set up logging configuration"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress noisy logs from libraries
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

def start_upload_api_thread(port=5005):
    """Start the upload API in a separate thread"""
    api_thread = threading.Thread(target=start_api, args=('0.0.0.0', port))
    api_thread.daemon = True
    api_thread.start()
    logging.info(f"Upload API started on port {port}")
    return api_thread

def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger('main')
    
    logger.info("=" * 50)
    logger.info("Starting Tax Law AI Agent")
    logger.info("=" * 50)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Tax Law AI Agent')
    parser.add_argument('--fetch-now', action='store_true', 
                      help='Fetch documents immediately')
    parser.add_argument('--rebuild-index', action='store_true',
                      help='Rebuild the entire index')
    parser.add_argument('--health-check', action='store_true',
                      help='Run health checks')
    parser.add_argument('--api-only', action='store_true',
                      help='Run only the upload API server')
    parser.add_argument('--config', type=str, default='src/config/sources.json',
                      help='Path to configuration file')
    parser.add_argument('--api-port', type=int, default=5005,
                      help='Port for the upload API server')
    
    args = parser.parse_args()
    
    # Run upload API
    api_thread = start_upload_api_thread(args.api_port)
    
    if args.api_only:
        logger.info("Running in API-only mode")
        try:
            # Keep the main thread alive
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Shutting down API server")
            sys.exit(0)
    
    # Initialize components
    logger.info("Initializing components")
    fetcher = DocumentFetcher(args.config)
    processor = DocumentProcessor()
    indexer = DocumentIndexer()
    health_monitor = HealthMonitor()
    
    # Run health checks if requested
    if args.health_check:
        logger.info("Running health checks")
        health_results = health_monitor.run_all_checks()
        logger.info(f"Health check results: {health_results}")
    
    # Fetch documents immediately if requested
    if args.fetch_now:
        logger.info("Fetching documents immediately")
        try:
            fetcher.fetch_all_documents()
            processed_files = processor.process_new_files()
            
            if processed_files:
                logger.info(f"Processing complete. {len(processed_files)} files processed.")
                indexer.index_documents(processed_files)
                logger.info("Indexing complete.")
            else:
                logger.info("No new files to process.")
        except Exception as e:
            logger.error(f"Error during immediate fetch: {str(e)}")
    
    # Rebuild index if requested
    if args.rebuild_index:
        logger.info("Rebuilding the entire index")
        try:
            indexer.rebuild_index()
        except Exception as e:
            logger.error(f"Error during index rebuild: {str(e)}")
    
    # Initialize and start scheduler
    logger.info("Initializing scheduler")
    scheduler = DocumentScheduler(args.config)
    
    scheduler.start()
    logger.info("Scheduler started")
    
    # Keep the script running
    try:
        logger.info("Agent is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down Tax Law AI Agent")
        scheduler.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
