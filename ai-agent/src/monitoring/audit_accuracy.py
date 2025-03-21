#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
audit_accuracy.py - Evaluates AI response accuracy against known tax law facts

This script:
1. Runs a series of test queries against the AI system
2. Compares results with verified tax law information
3. Identifies potential inaccuracies or hallucinations
4. Generates audit reports for human review

Usage:
    python audit_accuracy.py --test-set=basic
"""

import argparse
import datetime
import json
import logging
import os
import random
import re
import requests
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai_audit.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_audit")

# Configuration
DEFAULT_CONFIG = {
    "api_endpoint": "http://localhost:8080/api/query",
    "db_path": "../../../database/tax_laws.db",
    "test_sets_path": "../../../tests/accuracy_tests/",
    "report_path": "../../../reports/accuracy/",
    "threshold_score": 0.75,  # Minimum acceptable accuracy score (0-1)
    "alert_recipients": ["admin@example.com"]
}


@dataclass
class TestResult:
    """Stores the result of a single test query"""
    query_id: str
    query: str
    ai_response: str
    expected_content: List[str]  # Key phrases that should be present
    expected_citations: List[str]  # Citations that should be present
    accuracy_score: float
    citation_score: float
    errors: List[str]
    timestamp: str = datetime.datetime.now().isoformat()


class AIAccuracyAuditor:
    """Audit AI responses for factual accuracy and citation correctness"""
    
    def __init__(self, config_path=None):
        """Initialize the AI accuracy auditor with configuration"""
        self.config = DEFAULT_CONFIG
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config.update(json.load(f))
        
        # Create report directory if it doesn't exist
        os.makedirs(os.path.abspath(os.path.join(
            os.path.dirname(__file__), self.config['report_path'])), 
            exist_ok=True
        )
        
        # Initialize DB connection for ground truth data
        db_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), self.config['db_path']))
        self.conn = self._connect_db(db_path)
        
        # Test statistics
        self.test_stats = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "average_accuracy": 0.0,
            "average_citation_score": 0.0
        }
        
    def _connect_db(self, db_path):
        """Connect to SQLite database"""
        try:
            conn = sqlite3.connect(db_path)
            # Create audit results table if it doesn't exist
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_audit_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT,
                    query TEXT,
                    ai_response TEXT,
                    accuracy_score REAL,
                    citation_score REAL,
                    errors TEXT,
                    timestamp TIMESTAMP
                )
            ''')
            conn.commit()
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
    
    def load_test_set(self, test_set_name):
        """Load a specific test set from JSON file"""
        test_set_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            self.config['test_sets_path'], 
            f"{test_set_name}.json"
        ))
        
        if not os.path.exists(test_set_path):
            test_set_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 
                self.config['test_sets_path'], 
                "default.json"
            ))
            logger.warning(f"Test set {test_set_name} not found, using default")
            
            # Create default test set if it doesn't exist
            if not os.path.exists(test_set_path):
                os.makedirs(os.path.dirname(test_set_path), exist_ok=True)
                with open(test_set_path, 'w') as f:
                    json.dump({
                        "name": "default",
                        "description": "Default test set for basic tax law queries",
                        "tests": [
                            {
                                "id": "basic-001",
                                "query": "What is the standard deduction for a single filer in 2023?",
                                "expected_content": [
                                    "standard deduction", "single", "2023", "$13,850"
                                ],
                                "expected_citations": ["IRS Publication 501"]
                            },
                            {
                                "id": "basic-002",
                                "query": "When is the tax filing deadline for 2023 taxes?",
                                "expected_content": [
                                    "April 15", "2024"
                                ],
                                "expected_citations": ["IRS"]
                            }
                        ]
                    }, f, indent=2)
        
        try:
            with open(test_set_path, 'r') as f:
                test_set = json.load(f)
                logger.info(f"Loaded test set {test_set['name']} with {len(test_set['tests'])} tests")
                return test_set
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading test set: {e}")
            return {"name": "error", "tests": []}
    
    def query_ai_system(self, query):
        """Send a query to the AI system and get the response"""
        try:
            response = requests.post(
                self.config["api_endpoint"],
                json={"query": query},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["response"]
        except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error querying AI system: {e}")
            return f"ERROR: Failed to get response from AI system: {str(e)}"
    
    def evaluate_accuracy(self, response, expected_content):
        """Evaluate the accuracy of the AI response against expected content"""
        if not response or "ERROR:" in response:
            return 0.0, ["Failed to get valid response from AI"]
        
        # Count how many expected content items are present in the response
        found_items = 0
        errors = []
        
        for item in expected_content:
            if item.lower() in response.lower():
                found_items += 1
            else:
                errors.append(f"Missing expected content: {item}")
        
        if not expected_content:
            return 1.0, []  # No expected content specified
            
        accuracy = found_items / len(expected_content)
        return accuracy, errors
    
    def evaluate_citations(self, response, expected_citations):
        """Evaluate the citation accuracy in the AI response"""
        if not response or "ERROR:" in response:
            return 0.0, ["Failed to get valid response from AI"]
        
        # Count how many expected citations are present in the response
        found_citations = 0
        errors = []
        
        for citation in expected_citations:
            # Look for citation patterns
            citation_pattern = re.compile(
                rf'(?:cited|according to|based on|from|in)\s+.*{re.escape(citation)}', 
                re.IGNORECASE
            )
            
            # Also check for <cite> tags if using a citation format
            cite_tag_pattern = re.compile(
                rf'<cite[^>]*>.*{re.escape(citation)}.*</cite>', 
                re.IGNORECASE
            )
            
            if (citation.lower() in response.lower() or 
                citation_pattern.search(response) or 
                cite_tag_pattern.search(response)):
                found_citations += 1
            else:
                errors.append(f"Missing expected citation: {citation}")
        
        if not expected_citations:
            return 1.0, []  # No expected citations specified
            
        citation_score = found_citations / len(expected_citations)
        return citation_score, errors
    
    def run_test(self, test):
        """Run a single test and evaluate the result"""
        query = test["query"]
        logger.info(f"Running test {test['id']}: {query}")
        
        # Get AI response
        ai_response = self.query_ai_system(query)
        
        # Evaluate accuracy
        accuracy_score, accuracy_errors = self.evaluate_accuracy(
            ai_response, test.get("expected_content", [])
        )
        
        # Evaluate citations
        citation_score, citation_errors = self.evaluate_citations(
            ai_response, test.get("expected_citations", [])
        )
        
        # Combine errors
        all_errors = accuracy_errors + citation_errors
        
        # Store result
        result = TestResult(
            query_id=test["id"],
            query=query,
            ai_response=ai_response,
            expected_content=test.get("expected_content", []),
            expected_citations=test.get("expected_citations", []),
            accuracy_score=accuracy_score,
            citation_score=citation_score,
            errors=all_errors
        )
        
        # Save to database
        self._save_result(result)
        
        # Update statistics
        self.test_stats["total_tests"] += 1
        if accuracy_score >= self.config["threshold_score"] and citation_score >= self.config["threshold_score"]:
            self.test_stats["passed_tests"] += 1
        else:
            self.test_stats["failed_tests"] += 1
        
        # Log result
        log_level = logging.INFO if accuracy_score >= self.config["threshold_score"] else logging.WARNING
        logger.log(log_level, f"Test {test['id']} - Accuracy: {accuracy_score:.2f}, Citations: {citation_score:.2f}")
        if all_errors:
            logger.warning(f"Errors in test {test['id']}: {', '.join(all_errors)}")
        
        return result
    
    def _save_result(self, result):
        """Save test result to database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO ai_audit_results 
            (query_id, query, ai_response, accuracy_score, citation_score, errors, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.query_id,
            result.query,
            result.ai_response,
            result.accuracy_score,
            result.citation_score,
            json.dumps(result.errors),
            result.timestamp
        ))
        self.conn.commit()
    
    def run_test_set(self, test_set):
        """Run all tests in a test set"""
        results = []
        
        for test in test_set["tests"]:
            result = self.run_test(test)
            results.append(result)
            # Small delay to avoid overloading the API
            time.sleep(0.5)
        
        # Update aggregate statistics
        if results:
            self.test_stats["average_accuracy"] = sum(r.accuracy_score for r in results) / len(results)
            self.test_stats["average_citation_score"] = sum(r.citation_score for r in results) / len(results)
        
        return results
    
    def generate_audit_report(self, test_set_name, results):
        """Generate an audit report from test results"""
        report = {
            "test_set": test_set_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "total_tests": self.test_stats["total_tests"],
                "passed_tests": self.test_stats["passed_tests"],
                "failed_tests": self.test_stats["failed_tests"],
                "average_accuracy": self.test_stats["average_accuracy"],
                "average_citation_score": self.test_stats["average_citation_score"],
                "overall_status": "PASS" if (
                    self.test_stats["average_accuracy"] >= self.config["threshold_score"] and
                    self.test_stats["average_citation_score"] >= self.config["threshold_score"]
                ) else "FAIL"
            },
            "results": [
                {
                    "id": r.query_id,
                    "query": r.query,
                    "accuracy_score": r.accuracy_score,
                    "citation_score": r.citation_score,
                    "errors": r.errors,
                    "status": "PASS" if (
                        r.accuracy_score >= self.config["threshold_score"] and
                        r.citation_score >= self.config["threshold_score"]
                    ) else "FAIL"
                }
                for r in results
            ]
        }
        
        # Save report to file
        report_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            self.config["report_path"],
            f"audit_report_{test_set_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ))
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Audit report saved to {report_path}")
        
        # Check if alert is needed
        if report["summary"]["overall_status"] == "FAIL":
            self._send_alert(
                f"AI Accuracy Alert: Test set {test_set_name} failed",
                f"The AI system failed accuracy testing with an average score of {report['summary']['average_accuracy']:.2f}. See the full report at {report_path}"
            )
        
        return report
    
    def _send_alert(self, subject, message):
        """Send alert to configured recipients - placeholder for actual email/notification logic"""
        recipients = self.config["alert_recipients"]
        logger.info(f"ALERT: {subject} - Would send to {recipients}")
        logger.info(f"Alert message: {message}")
        # In a production system, this would integrate with email or notification systems
        # Example: send_email(recipients, subject, message)
    
    def run_random_sampling(self, sample_size=10):
        """Run tests on random queries from the database"""
        # Get random tax law questions from our database
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title FROM tax_laws ORDER BY RANDOM() LIMIT ?", (sample_size,))
        random_laws = cursor.fetchall()
        
        # Generate questions about these laws
        tests = []
        for i, (law_id, title) in enumerate(random_laws):
            tests.append({
                "id": f"random-{i+1:03d}",
                "query": f"What are the key provisions of {title}?",
                # We don't know exact expected content, so use minimal validation
                "expected_content": [title],
                "expected_citations": []
            })
        
        test_set = {
            "name": "random_sample",
            "description": "Random sampling of tax laws for accuracy testing",
            "tests": tests
        }
        
        return self.run_test_set(test_set)


def run_audit(args):
    """Main function to run the auditor with command line arguments"""
    auditor = AIAccuracyAuditor(args.config)
    
    if args.random_sample:
        # Run random sampling
        results = auditor.run_random_sampling(args.sample_size)
        auditor.generate_audit_report("random_sample", results)
    else:
        # Run specific test set
        test_set = auditor.load_test_set(args.test_set)
        results = auditor.run_test_set(test_set)
        auditor.generate_audit_report(test_set["name"], results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit AI system accuracy on tax law queries")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--test-set", default="basic", help="Name of test set to use")
    parser.add_argument("--random-sample", action="store_true", help="Run random sampling instead of test set")
    parser.add_argument("--sample-size", type=int, default=10, help="Size of random sample")
    
    args = parser.parse_args()
    run_audit(args)
