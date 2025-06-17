#!/usr/bin/env python3
"""
Google Discover Monitoring Tool

This script monitors multiple news websites for new articles and tracks their appearance in Google Discover.
"""
import os
import sys
import argparse
from scraper import DiscoverMonitor
from config import WEBSITES, GSC_CREDENTIALS_FILE

def check_requirements():
    """Check if all required files and configurations are present."""
    if not os.path.exists(GSC_CREDENTIALS_FILE) and os.getenv('GOOGLE_APPLICATION_CREDENTIALS') is None:
        print(f"Warning: Google Search Console credentials not found. "
              f"Please create a file named '{GSC_CREDENTIALS_FILE}' in the project root.")

    if not os.path.exists('data'):
        os.makedirs('data')

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Monitor websites for Google Discover content.')
    parser.add_argument('--limit', type=int, default=50,
                       help='Maximum number of articles to process per website (default: 50)')
    parser.add_argument('--output', type=str, default='data/discover_report.csv',
                       help='Output CSV file path (default: data/discover_report.csv)')
    return parser.parse_args()

def main():
    """Main function to run the monitor."""
    args = parse_arguments()
    check_requirements()
    
    print("=== Google Discover Monitoring Tool ===")
    print(f"Monitoring {len(WEBSITES)} websites")
    
    try:
        monitor = DiscoverMonitor()
        monitor.run()
        print("\nMonitoring complete. Check the data directory for results.")
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()