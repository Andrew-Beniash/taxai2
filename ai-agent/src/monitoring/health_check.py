"""
Health Monitor Module

This module handles health checks for the RAG system and indexes.
It ensures the system is functioning properly and data is up-to-date.
"""

import requests
import logging
import json
from datetime import datetime, timedelta
import os

class HealthMonitor:
    """Monitor the health of the RAG system and indexes"""
    
    def __init__(self, rag_api_url='http://localhost:5000/rag/health'):
        """Initialize with RAG API URL"""
        self.rag_api_url = rag_api_url
        self.log_dir = 'logs'
        self.stats_dir = 'data/stats'
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('health_monitor')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
            # Also log to file
            file_handler = logging.FileHandler(os.path.join(self.log_dir, 'health_checks.log'))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def check_rag_health(self):
        """Check if RAG system is healthy"""
        try:
            self.logger.info("Checking RAG system health")
            
            # TODO: Uncomment when RAG API is available
            # response = requests.get(self.rag_api_url, timeout=10)
            # if response.status_code == 200:
            #     self.logger.info("RAG system is healthy")
            #     return True
            # else:
            #     self.logger.error(f"RAG system health check failed: {response.text}")
            #     return False
            
            # For testing/development, simulate success
            self.logger.info("RAG system is healthy (simulated)")
            self._log_health_status("rag_system", True)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to RAG system: {str(e)}")
            self._log_health_status("rag_system", False, str(e))
            return False
    
    def check_index_freshness(self):
        """Check if index is fresh"""
        try:
            self.logger.info("Checking index freshness")
            
            index_stats_file = os.path.join(self.stats_dir, 'index_stats.json')
            if not os.path.exists(index_stats_file):
                self.logger.warning("No index stats found")
                self._log_health_status("index_freshness", False, "No index stats found")
                return False
            
            with open(index_stats_file, 'r') as f:
                stats = json.load(f)
            
            last_update = datetime.fromisoformat(stats.get('last_update', '2000-01-01T00:00:00'))
            now = datetime.now()
            
            # Check if index is older than 7 days
            if (now - last_update) > timedelta(days=7):
                self.logger.warning(f"Index is stale: last updated {last_update}")
                self._log_health_status("index_freshness", False, f"Index is stale: last updated {last_update}")
                return False
            
            self.logger.info(f"Index is fresh: last updated {last_update}")
            self._log_health_status("index_freshness", True)
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking index freshness: {str(e)}")
            self._log_health_status("index_freshness", False, str(e))
            return False
    
    def check_document_coverage(self):
        """Check if we have appropriate document coverage"""
        try:
            self.logger.info("Checking document coverage")
            
            # Count documents in the processed directory
            processed_dir = 'data/processed'
            if not os.path.exists(processed_dir):
                self.logger.warning("Processed directory not found")
                self._log_health_status("document_coverage", False, "Processed directory not found")
                return False
            
            # Count processed documents
            processed_files = [f for f in os.listdir(processed_dir) if f.endswith('.processed.txt')]
            doc_count = len(processed_files)
            
            # Check against minimum threshold
            min_threshold = 5  # Minimum number of documents expected
            if doc_count < min_threshold:
                self.logger.warning(f"Insufficient document coverage: only {doc_count} documents processed")
                self._log_health_status("document_coverage", False, f"Only {doc_count} documents")
                return False
            
            self.logger.info(f"Document coverage is adequate: {doc_count} documents processed")
            self._log_health_status("document_coverage", True, f"{doc_count} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking document coverage: {str(e)}")
            self._log_health_status("document_coverage", False, str(e))
            return False
    
    def run_all_checks(self):
        """Run all health checks"""
        self.logger.info("Running all health checks")
        
        results = {
            "rag_health": self.check_rag_health(),
            "index_freshness": self.check_index_freshness(),
            "document_coverage": self.check_document_coverage(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate overall health
        overall_health = all(results[key] for key in results if key != "timestamp")
        results["overall_health"] = overall_health
        
        # Save results
        health_log_path = os.path.join(self.stats_dir, 'health_status.json')
        with open(health_log_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Overall health status: {'HEALTHY' if overall_health else 'UNHEALTHY'}")
        return results
    
    def _log_health_status(self, check_name, status, details=None):
        """Log health check status to file"""
        health_log_dir = os.path.join(self.stats_dir, 'health_logs')
        os.makedirs(health_log_dir, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "check": check_name,
            "status": "PASS" if status else "FAIL"
        }
        
        if details:
            log_entry["details"] = details
        
        log_file = os.path.join(health_log_dir, f"{check_name}_log.jsonl")
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

# Simple test to run if this module is run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = HealthMonitor()
    results = monitor.run_all_checks()
    print(json.dumps(results, indent=2))
