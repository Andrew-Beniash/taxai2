#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
error_handler.py - Centralized error logging and notification system

This script:
1. Provides a unified error logging interface for the entire application
2. Categorizes errors by severity and type
3. Maintains error logs with context for debugging
4. Sends alerts for critical errors
5. Provides error trend analysis 

Usage:
    from error_handler import ErrorHandler
    error_handler = ErrorHandler()
    error_handler.log_error("Failed to retrieve tax data", "retrieval", context={"url": "https://irs.gov/..."})
"""

import argparse
import datetime
import json
import logging
import os
import re
import sqlite3
import sys
import time
import traceback
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Union, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system_errors.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("error_handler")

# Configuration
DEFAULT_CONFIG = {
    "db_path": "../../../database/error_logs.db",
    "log_file": "system_errors.log",
    "alert_threshold": {
        "critical": 1,      # Alert on first critical error
        "error": 5,         # Alert after 5 errors of same type in an hour
        "warning": 10       # Alert after 10 warnings of same type in an hour
    },
    "retention_days": 30,   # Keep error logs for 30 days
    "alert_recipients": ["admin@example.com"]
}


class ErrorSeverity(Enum):
    """Enum for error severity levels"""
    CRITICAL = "critical"   # System cannot function, immediate attention required
    ERROR = "error"         # Functionality broken, needs attention soon
    WARNING = "warning"     # Potential issue, should be reviewed
    INFO = "info"           # Informational message, no action needed


class ErrorCategory(Enum):
    """Enum for error categories"""
    RETRIEVAL = "retrieval"      # Data retrieval errors (HTTP, API, etc.)
    DATABASE = "database"        # Database connection or query errors
    EMBEDDING = "embedding"      # Vector embedding or FAISS errors
    PARSING = "parsing"          # Document parsing errors
    AI_RESPONSE = "ai_response"  # AI model or generation errors
    SYSTEM = "system"            # General system errors (disk, memory, etc.)
    VALIDATION = "validation"    # Data validation errors
    OTHER = "other"              # Uncategorized errors


@dataclass
class ErrorRecord:
    """Data structure for error records"""
    timestamp: str
    severity: str
    category: str
    message: str
    source: str
    context: Dict[str, Any]
    stack_trace: str
    error_hash: str = ""  # Unique hash for grouping similar errors


class ErrorHandler:
    """Centralized error logging and notification system"""
    
    def __init__(self, config_path=None):
        """Initialize the error handler with configuration"""
        self.config = DEFAULT_CONFIG
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config.update(json.load(f))
        
        # Initialize DB connection
        db_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), self.config["db_path"]))
        self.conn = self._connect_db(db_path)
        
        # Error counters for tracking thresholds
        self.error_counts = {
            ErrorSeverity.CRITICAL.value: {},
            ErrorSeverity.ERROR.value: {},
            ErrorSeverity.WARNING.value: {}
        }
        
        # Ensure log directory exists
        log_dir = os.path.dirname(os.path.abspath(self.config["log_file"]))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    def _connect_db(self, db_path):
        """Connect to SQLite database and initialize tables"""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create error_logs table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    severity TEXT,
                    category TEXT,
                    message TEXT,
                    source TEXT,
                    context TEXT,
                    stack_trace TEXT,
                    error_hash TEXT
                )
            ''')
            
            # Create error_trends table for aggregated error statistics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    severity TEXT,
                    category TEXT,
                    error_hash TEXT,
                    count INTEGER
                )
            ''')
            
            conn.commit()
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            # Fall back to file-based logging if DB connection fails
            return None
    
    def _generate_error_hash(self, message, category, stack_trace=None):
        """Generate a unique hash for an error to group similar ones"""
        # Remove variable parts from message (dates, IDs, etc.)
        clean_message = re.sub(r'\d+', 'N', message)
        clean_message = re.sub(r'\'[^\']*\'', "'X'", clean_message)
        
        # Get the first line of stack trace if available (most relevant part)
        trace_line = ""
        if stack_trace:
            trace_lines = stack_trace.split('\n')
            if len(trace_lines) > 1:
                trace_line = trace_lines[-2]  # Usually the most specific line
        
        # Combine and hash
        import hashlib
        hash_input = f"{category}:{clean_message}:{trace_line}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def log_error(self, message, category, severity=ErrorSeverity.ERROR, context=None, source=None):
        """Log an error with context and optionally send alerts"""
        if isinstance(severity, str):
            severity = next((sev for sev in ErrorSeverity if sev.value == severity), ErrorSeverity.ERROR)
        
        if isinstance(category, str):
            category = next((cat for cat in ErrorCategory if cat.value == category), ErrorCategory.OTHER)
        
        # Get current stack trace
        stack_trace = traceback.format_exc() if sys.exc_info()[0] else ""
        
        # Generate error hash
        error_hash = self._generate_error_hash(message, category.value, stack_trace)
        
        # Create error record
        error_record = ErrorRecord(
            timestamp=datetime.datetime.now().isoformat(),
            severity=severity.value,
            category=category.value,
            message=message,
            source=source or self._get_caller_info(),
            context=context or {},
            stack_trace=stack_trace,
            error_hash=error_hash
        )
        
        # Log to database
        self._log_to_db(error_record)
        
        # Log to file
        self._log_to_file(error_record)
        
        # Check if we need to send an alert
        self._check_alert_threshold(error_record)
        
        return error_record
    
    def _log_to_db(self, error_record):
        """Store error record in database"""
        if not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO error_logs (timestamp, severity, category, message, source, context, stack_trace, error_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    error_record.timestamp,
                    error_record.severity,
                    error_record.category,
                    error_record.message,
                    error_record.source,
                    json.dumps(error_record.context),
                    error_record.stack_trace,
                    error_record.error_hash
                )
            )
            
            # Update trends table
            date = error_record.timestamp.split("T")[0]  # Get just the date part
            cursor.execute(
                "INSERT OR IGNORE INTO error_trends (date, severity, category, error_hash, count) "
                "VALUES (?, ?, ?, ?, 0)",
                (date, error_record.severity, error_record.category, error_record.error_hash)
            )
            cursor.execute(
                "UPDATE error_trends SET count = count + 1 "
                "WHERE date = ? AND severity = ? AND category = ? AND error_hash = ?",
                (date, error_record.severity, error_record.category, error_record.error_hash)
            )
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            # Log to standard logger if DB insert fails
            logger.error(f"Failed to log error to database: {e}")
    
    def _log_to_file(self, error_record):
        """Log error to file in a structured format"""
        try:
            log_entry = {
                "timestamp": error_record.timestamp,
                "severity": error_record.severity,
                "category": error_record.category,
                "message": error_record.message,
                "source": error_record.source,
                "context": error_record.context,
                "error_hash": error_record.error_hash
            }
            
            # Add stack trace only if it exists
            if error_record.stack_trace:
                log_entry["stack_trace"] = error_record.stack_trace
            
            # Log to file
            with open(self.config["log_file"], "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            # Last resort: log to standard logger
            logger.error(f"Failed to log error to file: {e}")
            logger.error(f"Original error: {error_record.message}")
    
    def _get_caller_info(self):
        """Get information about the calling function/module"""
        stack = traceback.extract_stack()
        # Look for the first frame that isn't in this file
        for frame in reversed(stack[:-1]):  # Skip this function
            filename = os.path.basename(frame.filename)
            if filename != os.path.basename(__file__):
                return f"{filename}:{frame.lineno} in {frame.name}"
        return "unknown"
    
    def _check_alert_threshold(self, error_record):
        """Check if we should send an alert based on error frequency"""
        severity = error_record.severity
        error_hash = error_record.error_hash
        
        # Initialize counter if needed
        if error_hash not in self.error_counts[severity]:
            self.error_counts[severity][error_hash] = {
                "count": 0,
                "first_seen": datetime.datetime.now(),
                "last_alerted": None
            }
        
        # Update counter
        self.error_counts[severity][error_hash]["count"] += 1
        
        # Check if we need to send an alert
        counter = self.error_counts[severity][error_hash]
        threshold = self.config["alert_threshold"][severity]
        
        # Calculate time since first error
        time_window = datetime.datetime.now() - counter["first_seen"]
        
        # Check if we're within the alert window (1 hour) and have exceeded threshold
        if time_window.total_seconds() <= 3600 and counter["count"] >= threshold:
            # Check if we've already alerted recently (avoid alert spam)
            if (counter["last_alerted"] is None or 
                (datetime.datetime.now() - counter["last_alerted"]).total_seconds() > 1800):  # 30 min
                self._send_alert(error_record, counter["count"])
                counter["last_alerted"] = datetime.datetime.now()
                counter["count"] = 0  # Reset counter
                counter["first_seen"] = datetime.datetime.now()  # Reset window
        
        # Reset counter if window has expired
        elif time_window.total_seconds() > 3600:
            counter["count"] = 1
            counter["first_seen"] = datetime.datetime.now()
    
    def _send_alert(self, error_record, count):
        """Send an alert for critical errors"""
        severity_upper = error_record.severity.upper()
        subject = f"{severity_upper} ALERT: {error_record.category} error occurred {count} time(s)"
        
        message = f"""
Error Details:
-------------
Severity: {error_record.severity}
Category: {error_record.category}
Message: {error_record.message}
Source: {error_record.source}
Timestamp: {error_record.timestamp}
Count: {count} occurrence(s) in the last hour
        """
        
        if error_record.context:
            message += f"\nContext: {json.dumps(error_record.context, indent=2)}"
        
        if error_record.stack_trace:
            message += f"\nStack Trace:\n{error_record.stack_trace}"
        
        # Get similar errors
        similar_errors = self._get_similar_errors(error_record.error_hash, limit=3)
        if similar_errors:
            message += "\n\nSimilar Recent Errors:\n"
            for i, err in enumerate(similar_errors):
                message += f"{i+1}. {err['timestamp']} - {err['message']}\n"
        
        logger.info(f"ALERT: {subject} - Would send to {self.config['alert_recipients']}")
        logger.info(f"Alert message: {message}")
        
        # In a production system, this would integrate with email or notification systems
        # Example: send_email(self.config['alert_recipients'], subject, message)
    
    def _get_similar_errors(self, error_hash, limit=3):
        """Get similar errors from the database"""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT timestamp, message FROM error_logs "
                "WHERE error_hash = ? ORDER BY timestamp DESC LIMIT ?",
                (error_hash, limit)
            )
            return [{"timestamp": row[0], "message": row[1]} for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def cleanup_old_errors(self):
        """Remove error logs older than retention period"""
        if not self.conn:
            return 0
        
        retention_days = self.config["retention_days"]
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=retention_days)).isoformat()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM error_logs WHERE timestamp < ?", (cutoff_date,))
            deleted_count = cursor.rowcount
            
            # Also cleanup trends table for dates older than retention period
            cutoff_date_short = cutoff_date.split("T")[0]  # Just the date part
            cursor.execute("DELETE FROM error_trends WHERE date < ?", (cutoff_date_short,))
            
            self.conn.commit()
            logger.info(f"Cleaned up {deleted_count} error logs older than {retention_days} days")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"Failed to clean up old error logs: {e}")
            return 0
    
    def get_error_trends(self, days=7, categories=None):
        """Get error trends for the last N days"""
        if not self.conn:
            return {}
        
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        
        category_filter = ""
        params = [start_date]
        
        if categories:
            placeholders = ", ".join(["?"] * len(categories))
            category_filter = f"AND category IN ({placeholders})"
            params.extend(categories)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"SELECT date, severity, category, SUM(count) FROM error_trends "
                f"WHERE date >= ? {category_filter} "
                f"GROUP BY date, severity, category "
                f"ORDER BY date",
                params
            )
            
            results = cursor.fetchall()
            
            # Organize data by date, then severity, then category
            trends = {}
            for row in results:
                date, severity, category, count = row
                
                if date not in trends:
                    trends[date] = {}
                
                if severity not in trends[date]:
                    trends[date][severity] = {}
                
                trends[date][severity][category] = count
            
            return trends
        except sqlite3.Error as e:
            logger.error(f"Failed to get error trends: {e}")
            return {}
    
    def get_most_frequent_errors(self, days=1, limit=10):
        """Get the most frequent errors in the last N days"""
        if not self.conn:
            return []
        
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT error_hash, severity, category, message, COUNT(*) as count "
                "FROM error_logs "
                "WHERE timestamp >= ? "
                "GROUP BY error_hash "
                "ORDER BY count DESC "
                "LIMIT ?",
                (start_date, limit)
            )
            
            return [
                {
                    "error_hash": row[0],
                    "severity": row[1],
                    "category": row[2],
                    "message": row[3],
                    "count": row[4]
                }
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            logger.error(f"Failed to get most frequent errors: {e}")
            return []
    
    def get_retrieval_errors(self, days=1, limit=20):
        """Get recent retrieval errors specifically"""
        if not self.conn:
            return []
        
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT timestamp, message, context, stack_trace "
                "FROM error_logs "
                "WHERE timestamp >= ? AND category = ? "
                "ORDER BY timestamp DESC "
                "LIMIT ?",
                (start_date, ErrorCategory.RETRIEVAL.value, limit)
            )
            
            return [
                {
                    "timestamp": row[0],
                    "message": row[1],
                    "context": json.loads(row[2]) if row[2] else {},
                    "stack_trace": row[3] if row[3] else ""
                }
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            logger.error(f"Failed to get retrieval errors: {e}")
            return []


def run_cleanup(args):
    """Run error log cleanup"""
    handler = ErrorHandler(args.config)
    deleted = handler.cleanup_old_errors()
    print(f"Cleaned up {deleted} old error logs")


def run_report(args):
    """Generate error reports"""
    handler = ErrorHandler(args.config)
    
    if args.trends:
        # Generate trends report
        trends = handler.get_error_trends(days=args.days)
        print(f"Error trends for the last {args.days} days:")
        print(json.dumps(trends, indent=2))
    
    if args.frequent:
        # Generate most frequent errors report
        frequent = handler.get_most_frequent_errors(days=args.days, limit=args.limit)
        print(f"Most frequent errors in the last {args.days} days:")
        for i, err in enumerate(frequent):
            print(f"{i+1}. [{err['severity']}] {err['category']}: {err['message']} ({err['count']} occurrences)")
    
    if args.retrieval:
        # Generate retrieval errors report
        retrieval = handler.get_retrieval_errors(days=args.days, limit=args.limit)
        print(f"Recent retrieval errors in the last {args.days} days:")
        for i, err in enumerate(retrieval):
            print(f"{i+1}. {err['timestamp']} - {err['message']}")
            if err['context']:
                print(f"   Context: {json.dumps(err['context'], indent=2)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Error handling and reporting system")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old error logs")
    cleanup_parser.add_argument("--config", help="Path to configuration file")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate error reports")
    report_parser.add_argument("--config", help="Path to configuration file")
    report_parser.add_argument("--days", type=int, default=7, help="Number of days to include in report")
    report_parser.add_argument("--limit", type=int, default=10, help="Maximum number of errors to show")
    report_parser.add_argument("--trends", action="store_true", help="Show error trends")
    report_parser.add_argument("--frequent", action="store_true", help="Show most frequent errors")
    report_parser.add_argument("--retrieval", action="store_true", help="Show retrieval errors specifically")
    
    args = parser.parse_args()
    
    if args.command == "cleanup":
        run_cleanup(args)
    elif args.command == "report":
        run_report(args)
    else:
        parser.print_help()
