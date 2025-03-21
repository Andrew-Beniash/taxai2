#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
monitor_data.py - Tracks tax law updates and detects outdated laws

This script:
1. Periodically scans IRS and tax court databases for updates
2. Compares against existing tax law data in the database
3. Flags outdated or superseded tax laws
4. Generates reports on data freshness

Usage:
    python monitor_data.py --check-frequency=daily
"""

import argparse
import datetime
import json
import logging
import os
import requests
import sqlite3
import time
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tax_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("tax_monitor")

# Configuration
DEFAULT_CONFIG = {
    "irs_sources": [
        {"url": "https://www.irs.gov/newsroom", "type": "news"},
        {"url": "https://www.irs.gov/tax-professionals/tax-code-regulations-and-official-guidance", "type": "regulations"}
    ],
    "court_sources": [
        {"url": "https://www.ustaxcourt.gov/opinions.html", "type": "opinions"},
        {"url": "https://www.supremecourt.gov/opinions/opinions.aspx", "type": "supreme_court"}
    ],
    "check_frequency": 86400,  # 24 hours in seconds
    "outdated_threshold_days": 365,  # Consider laws older than 1 year for review
    "db_path": "../../../database/tax_laws.db",
    "alert_recipients": ["admin@example.com"]
}


class TaxDataMonitor:
    """Monitor tax law data sources for freshness and updates"""
    
    def __init__(self, config_path=None):
        """Initialize the tax data monitor with configuration"""
        self.config = DEFAULT_CONFIG
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config.update(json.load(f))
        
        # Initialize DB connection
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), self.config['db_path']))
        self.conn = self._connect_db(db_path)
        
        # Last check timestamp
        self.last_checked = {}
        
    def _connect_db(self, db_path):
        """Connect to SQLite database"""
        try:
            conn = sqlite3.connect(db_path)
            # Create tables if they don't exist
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_source_tracking (
                    url TEXT PRIMARY KEY,
                    last_checked TIMESTAMP,
                    last_updated TIMESTAMP,
                    status TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outdated_laws (
                    law_id INTEGER,
                    title TEXT,
                    publication_date TIMESTAMP,
                    superseded_by TEXT,
                    flag_date TIMESTAMP,
                    status TEXT
                )
            ''')
            conn.commit()
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
            
    def fetch_source_data(self, source):
        """Fetch data from a source URL"""
        try:
            logger.info(f"Checking source: {source['url']}")
            response = requests.get(source['url'], timeout=30)
            response.raise_for_status()
            
            # Update source tracking
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO data_source_tracking VALUES (?, ?, ?, ?)",
                (source['url'], datetime.datetime.now(), None, "active")
            )
            self.conn.commit()
            
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {source['url']}: {e}")
            # Update source status
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE data_source_tracking SET status = ? WHERE url = ?",
                ("error", source['url'])
            )
            self.conn.commit()
            return None
            
    def parse_irs_updates(self, html_content, source_type):
        """Parse IRS website HTML to extract updates"""
        if not html_content:
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        updates = []
        
        if source_type == "news":
            # Parse news items
            news_items = soup.find_all("div", class_="news-item")
            for item in news_items:
                title_elem = item.find("h3") or item.find("h2")
                date_elem = item.find("time") or item.find("span", class_="date")
                
                if title_elem and date_elem:
                    updates.append({
                        "title": title_elem.text.strip(),
                        "date": parse_date(date_elem.text.strip()),
                        "url": item.find("a")["href"] if item.find("a") else "",
                        "source_type": source_type
                    })
        
        elif source_type == "regulations":
            # Parse regulation items
            reg_items = soup.find_all("div", class_="regulation-item") or soup.find_all("li", class_="item")
            for item in reg_items:
                title_elem = item.find("h3") or item.find("a")
                # Dates might be in different formats
                date_text = ""
                date_elem = item.find("time") or item.find("span", class_="date")
                if date_elem:
                    date_text = date_elem.text.strip()
                
                if title_elem:
                    try:
                        date_obj = parse_date(date_text) if date_text else datetime.datetime.now()
                        updates.append({
                            "title": title_elem.text.strip(),
                            "date": date_obj,
                            "url": item.find("a")["href"] if item.find("a") else "",
                            "source_type": source_type
                        })
                    except (ValueError, TypeError):
                        # If date parsing fails, skip this update
                        continue
                        
        return updates
    
    def parse_court_updates(self, html_content, source_type):
        """Parse court website HTML to extract updates"""
        if not html_content:
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        updates = []
        
        if source_type == "opinions":
            # Parse opinion items
            opinion_items = soup.find_all("tr") or soup.find_all("div", class_="opinion-item")
            for item in opinion_items:
                # Look for date and title elements - structure varies by court
                date_elem = item.find("td", class_="date") or item.find("span", class_="date")
                title_elem = item.find("td", class_="case") or item.find("a", class_="title")
                
                if title_elem and date_elem:
                    try:
                        date_obj = parse_date(date_elem.text.strip())
                        updates.append({
                            "title": title_elem.text.strip(),
                            "date": date_obj,
                            "url": item.find("a")["href"] if item.find("a") else "",
                            "source_type": source_type
                        })
                    except (ValueError, TypeError):
                        continue
        
        return updates
    
    def check_for_updates(self):
        """Check all configured sources for updates"""
        all_updates = []
        
        # Check IRS sources
        for source in self.config["irs_sources"]:
            html_content = self.fetch_source_data(source)
            if html_content:
                updates = self.parse_irs_updates(html_content, source["type"])
                all_updates.extend(updates)
                
        # Check court sources
        for source in self.config["court_sources"]:
            html_content = self.fetch_source_data(source)
            if html_content:
                updates = self.parse_court_updates(html_content, source["type"])
                all_updates.extend(updates)
        
        logger.info(f"Found {len(all_updates)} updates across all sources")
        return all_updates
    
    def detect_outdated_laws(self):
        """Identify potentially outdated laws based on age and updates"""
        cursor = self.conn.cursor()
        threshold_date = datetime.datetime.now() - datetime.timedelta(days=self.config["outdated_threshold_days"])
        
        # Find laws older than the threshold
        cursor.execute('''
            SELECT id, title, publication_date FROM tax_laws 
            WHERE publication_date < ? AND id NOT IN (SELECT law_id FROM outdated_laws)
        ''', (threshold_date.isoformat(),))
        
        old_laws = cursor.fetchall()
        logger.info(f"Found {len(old_laws)} potentially outdated laws")
        
        # Flag them for review
        for law in old_laws:
            cursor.execute('''
                INSERT INTO outdated_laws (law_id, title, publication_date, flag_date, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (law[0], law[1], law[2], datetime.datetime.now().isoformat(), "needs_review"))
        
        self.conn.commit()
        return old_laws
    
    def generate_freshness_report(self):
        """Generate a report on data freshness"""
        cursor = self.conn.cursor()
        
        # Get source freshness
        cursor.execute("SELECT url, last_checked, status FROM data_source_tracking")
        sources = cursor.fetchall()
        
        # Get outdated laws counts
        cursor.execute("SELECT status, COUNT(*) FROM outdated_laws GROUP BY status")
        outdated_stats = cursor.fetchall()
        
        report = {
            "report_date": datetime.datetime.now().isoformat(),
            "sources": [{"url": s[0], "last_checked": s[1], "status": s[2]} for s in sources],
            "outdated_laws": {s[0]: s[1] for s in outdated_stats},
            "total_laws": 0
        }
        
        # Get total count of laws
        cursor.execute("SELECT COUNT(*) FROM tax_laws")
        report["total_laws"] = cursor.fetchone()[0]
        
        return report
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        logger.info("Starting monitoring cycle")
        
        # Check for updates
        updates = self.check_for_updates()
        
        # Flag potential outdated laws
        outdated = self.detect_outdated_laws()
        
        # Generate report
        report = self.generate_freshness_report()
        
        # Log report summary
        logger.info(f"Monitoring cycle complete: {len(updates)} updates, {len(outdated)} outdated laws flagged")
        
        # Optionally, send alerts if sources are broken
        self._check_for_broken_sources()
        
        return report
    
    def _check_for_broken_sources(self):
        """Check for any broken data sources and send alerts"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM data_source_tracking WHERE status = 'error'")
        broken_sources = [row[0] for row in cursor.fetchall()]
        
        if broken_sources:
            logger.warning(f"Found {len(broken_sources)} broken sources: {broken_sources}")
            self._send_alert(f"Data source alert: {len(broken_sources)} broken sources detected", 
                            f"The following sources are unavailable: {', '.join(broken_sources)}")
    
    def _send_alert(self, subject, message):
        """Send alert to configured recipients - placeholder for actual email/notification logic"""
        recipients = self.config["alert_recipients"]
        logger.info(f"ALERT: {subject} - Would send to {recipients}")
        logger.info(f"Alert message: {message}")
        # In a production system, this would integrate with email or notification systems
        # Example: send_email(recipients, subject, message)


def run_monitor(args):
    """Main function to run the monitor with command line arguments"""
    monitor = TaxDataMonitor(args.config)
    
    if args.run_once:
        # Run once and exit
        monitor.run_monitoring_cycle()
    else:
        # Run continuously
        while True:
            monitor.run_monitoring_cycle()
            logger.info(f"Sleeping for {args.check_frequency} seconds")
            time.sleep(args.check_frequency)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor tax data sources for updates and freshness")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--check-frequency", type=int, default=86400, 
                        help="Check frequency in seconds (default: 86400 - daily)")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    run_monitor(args)
