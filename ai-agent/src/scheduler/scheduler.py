"""
Document Scheduler Module

This module handles scheduling periodic tasks for document retrieval and indexing.
It uses APScheduler to run jobs at specified intervals.
"""

import json
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os

# Import our components
from src.fetcher.document_fetcher import DocumentFetcher
from src.preprocessing.processor import DocumentProcessor
from src.indexing.indexer import DocumentIndexer
from src.monitoring.health_check import HealthMonitor

class DocumentScheduler:
    """Schedule periodic tasks for document retrieval and indexing"""
    
    def __init__(self, config_path='src/config/sources.json'):
        """Initialize scheduler with configuration"""
        self.scheduler = BackgroundScheduler()
        self.config_path = config_path
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.fetcher = DocumentFetcher(config_path)
        self.processor = DocumentProcessor()
        self.indexer = DocumentIndexer()
        
        # Set up logging
        self.logger = logging.getLogger('document_scheduler')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def start(self):
        """Start all scheduled jobs"""
        self.logger.info("Starting document scheduler")
        
        # Schedule daily jobs
        self._schedule_by_frequency('daily', hour=2, minute=0)
        
        # Schedule weekly jobs
        self._schedule_by_frequency('weekly', day_of_week='mon', hour=3, minute=0)
        
        # Schedule monthly jobs
        self._schedule_by_frequency('monthly', day=1, hour=4, minute=0)
        
        # Add health check job
        self.scheduler.add_job(
            self._check_health,
            'interval',
            hours=1,
            id="health_check"
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.logger.info("Document scheduler started successfully")
    
    def _schedule_by_frequency(self, frequency, **cron_args):
        """Schedule jobs based on frequency"""
        sources = []
        for source, freq in self.config['updateFrequency'].items():
            if freq.lower() == frequency.lower():
                sources.append(source)
        
        if not sources:
            return
        
        for source in sources:
            job_id = f"{frequency}_{source.replace(' ', '_')}"
            self.scheduler.add_job(
                self._fetch_and_index_for_source,
                CronTrigger(**cron_args),
                args=[source],
                id=job_id
            )
            self.logger.info(f"Scheduled {frequency} job for {source}")
    
    def _fetch_and_index_for_source(self, source_name):
        """Fetch and index documents for a specific source"""
        self.logger.info(f"Starting scheduled update for {source_name}")
        
        try:
            # Filter documents by source
            source_docs = [doc for doc in self.config['documents'] 
                        if doc.get('source') in source_name]
            
            if not source_docs:
                self.logger.warning(f"No documents configured for source: {source_name}")
                return
            
            successful_fetches = 0
            for doc in source_docs:
                try:
                    self.fetcher.fetch_document(doc)
                    successful_fetches += 1
                except Exception as e:
                    self.logger.error(f"Error fetching document {doc['url']}: {str(e)}")
            
            if successful_fetches > 0:
                # Process newly downloaded files
                self.logger.info("Processing downloaded files")
                processed_files = self.processor.process_new_files()
                
                # Index processed files
                if processed_files:
                    self.logger.info(f"Indexing {len(processed_files)} processed files")
                    self.indexer.index_documents(processed_files)
                    self.logger.info("Indexing complete")
                else:
                    self.logger.info("No new files to index")
            
            self.logger.info(f"Completed scheduled update for {source_name}")
            
        except Exception as e:
            self.logger.error(f"Error in scheduled update for {source_name}: {str(e)}")
    
    def _check_health(self):
        """Run health checks"""
        try:
            monitor = HealthMonitor()
            rag_health = monitor.check_rag_health()
            index_freshness = monitor.check_index_freshness()
            
            if not rag_health or not index_freshness:
                self.logger.warning("Health check failed, consider troubleshooting the system")
            else:
                self.logger.info("Health check passed successfully")
        except Exception as e:
            self.logger.error(f"Error during health check: {str(e)}")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        self.logger.info("Document scheduler stopped")
    
    def run_now(self, source_name=None):
        """Run a job immediately"""
        if source_name:
            self.logger.info(f"Running immediate update for {source_name}")
            self._fetch_and_index_for_source(source_name)
        else:
            self.logger.info("Running immediate update for all sources")
            # Run for all configured frequencies
            for source in self.config['updateFrequency'].keys():
                self._fetch_and_index_for_source(source)
        
        self.logger.info("Immediate update completed")

# Simple test to run if this module is run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler = DocumentScheduler()
    
    # Run immediately for testing
    scheduler.run_now()
    
    # Uncomment to start the scheduler
    # scheduler.start()
    # 
    # # Keep the script running
    # try:
    #     while True:
    #         time.sleep(60)
    # except KeyboardInterrupt:
    #     scheduler.stop()
