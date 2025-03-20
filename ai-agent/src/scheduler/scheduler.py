"""
This module provides scheduling functionality for periodic tax law updates.
It uses APScheduler to automate the fetching and processing of tax law documents
at regular intervals.
"""

import logging
import time
import signal
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import configuration
from src.config import FETCH_INTERVAL_HOURS, CLEANUP_INTERVAL_DAYS

# Initialize logger
logger = logging.getLogger('ai_tax_agent.scheduler')


class TaxLawUpdateScheduler:
    """Scheduler for automating tax law updates."""
    
    def __init__(self, fetcher, processor):
        """
        Initialize the scheduler with the fetcher and processor components.
        
        Args:
            fetcher: An instance of IRSUpdateFetcher for fetching updates
            processor: An instance of DocumentProcessor for processing documents
        """
        self.fetcher = fetcher
        self.processor = processor
        self.scheduler = BackgroundScheduler()
        self.setup_jobs()
    
    def setup_jobs(self):
        """Set up scheduled jobs for fetching and processing tax law updates."""
        # Job for fetching and processing tax law updates
        self.scheduler.add_job(
            self.fetch_and_process_updates,
            trigger=IntervalTrigger(hours=FETCH_INTERVAL_HOURS),
            id='fetch_updates',
            name='Fetch Tax Law Updates',
            replace_existing=True,
            next_run_time=datetime.now()  # Run immediately on startup
        )
        
        # Job for cleaning outdated documents
        self.scheduler.add_job(
            self.clean_outdated_documents,
            trigger=CronTrigger(day_of_week='mon', hour=2, minute=0),  # Run weekly on Monday at 2 AM
            id='clean_documents',
            name='Clean Outdated Documents',
            replace_existing=True
        )
        
        # Add a status reporting job
        self.scheduler.add_job(
            self.report_status,
            trigger=IntervalTrigger(days=1),  # Daily status report
            id='status_report',
            name='Status Report',
            replace_existing=True,
            next_run_time=datetime.now() + timedelta(minutes=5)  # First run after 5 minutes
        )
        
        logger.info("Scheduled jobs setup completed")
    
    def fetch_and_process_updates(self):
        """Fetch and process tax law updates."""
        try:
            logger.info("Starting scheduled fetch and process job")
            start_time = time.time()
            
            # Fetch updates from all sources
            updates = self.fetcher.fetch_all_updates()
            
            if updates:
                logger.info(f"Found {len(updates)} new tax law updates, processing...")
                # Process downloaded documents
                processed_count = self.processor.process_documents(updates)
                logger.info(f"Successfully processed {processed_count} documents")
            else:
                logger.info("No new tax law updates found")
            
            elapsed_time = time.time() - start_time
            logger.info(f"Completed fetch and process job in {elapsed_time:.2f} seconds")
        
        except Exception as e:
            logger.error(f"Error in fetch and process job: {e}")
    
    def clean_outdated_documents(self):
        """Clean outdated documents from the database."""
        try:
            logger.info("Starting scheduled document cleanup job")
            
            # Clean documents older than the specified threshold
            removed_count = self.processor.clean_outdated_documents(days_threshold=CLEANUP_INTERVAL_DAYS)
            
            logger.info(f"Document cleanup completed, removed {removed_count} outdated documents")
        
        except Exception as e:
            logger.error(f"Error in document cleanup job: {e}")
    
    def report_status(self):
        """Generate and log a status report."""
        try:
            logger.info("Generating status report")
            
            # Here you could add code to generate a more detailed status report,
            # such as counting documents in the database, checking disk usage, etc.
            
            logger.info("Status report: AI Tax Law Fetcher Agent is running normally")
        
        except Exception as e:
            logger.error(f"Error generating status report: {e}")
    
    def start(self):
        """Start the scheduler."""
        try:
            logger.info("Starting Tax Law Update Scheduler")
            self.scheduler.start()
            
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._handle_shutdown)
            signal.signal(signal.SIGTERM, self._handle_shutdown)
            
            # Keep the main thread alive (if run directly)
            while True:
                time.sleep(1)
        
        except (KeyboardInterrupt, SystemExit):
            self.shutdown()
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals (SIGINT, SIGTERM)."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Shutdown the scheduler and perform cleanup."""
        logger.info("Shutting down Tax Law Update Scheduler")
        self.scheduler.shutdown()


if __name__ == "__main__":
    # Setup basic logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Import required components
    from src.fetcher.fetch_irs_updates import IRSUpdateFetcher
    from src.preprocessing.preprocess_documents import DocumentProcessor
    
    # Create components
    fetcher = IRSUpdateFetcher()
    processor = DocumentProcessor()
    
    # Create and start scheduler (will run once immediately)
    scheduler = TaxLawUpdateScheduler(fetcher, processor)
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nShutting down scheduler...")
        scheduler.shutdown()
