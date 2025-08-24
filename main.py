#!/usr/bin/env python3

import os
import argparse
from datetime import datetime
from login import login_to_procare, load_credentials
from dashboard_scraper import download_all_media

def main():
    """
    Main script to login to ProCare and download all photos and videos
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Download photos and videos from ProCare Connect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python main.py                                    # Download all media
  python main.py --from 2025-08-01 --to 2025-08-31 # Download August 2025 only
  python main.py --from 2025-08-20                  # Download from Aug 20 onwards
  python main.py --to 2025-08-15                    # Download up to Aug 15"""
    )
    
    parser.add_argument(
        '--from', '--start', dest='date_from',
        help='Start date for download range (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--to', '--end', dest='date_to', 
        help='End date for download range (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--dir', dest='download_dir', default='downloads',
        help='Base download directory (default: downloads)'
    )
    
    args = parser.parse_args()
    
    # Validate date formats if provided
    if args.date_from:
        try:
            datetime.strptime(args.date_from, '%Y-%m-%d')
        except ValueError:
            print("Error: --from date must be in YYYY-MM-DD format")
            return 1
    
    if args.date_to:
        try:
            datetime.strptime(args.date_to, '%Y-%m-%d')
        except ValueError:
            print("Error: --to date must be in YYYY-MM-DD format")
            return 1
    
    print("ProCare Photo & Video Downloader")
    print("=" * 40)
    
    if args.date_from or args.date_to:
        date_range = f"from {args.date_from or 'beginning'} to {args.date_to or 'now'}"
        print(f"Date range: {date_range}")
        print("-" * 40)
    
    # Load credentials
    print("Loading credentials...")
    creds = load_credentials()
    
    if not all(creds.values()):
        print("Error: Missing credentials in .env.secrets file")
        return
    
    # Login
    print("Logging in to ProCare...")
    auth_data = login_to_procare(creds['username'], creds['password'])
    
    if not auth_data:
        print("Login failed. Cannot proceed with download.")
        return
    
    # Download photos and videos
    print("\nFetching and downloading photos and videos...")
    download_summary = download_all_media(
        auth_data, 
        download_dir=args.download_dir,
        date_from=args.date_from,
        date_to=args.date_to
    )
    
    print("\n" + "=" * 30)
    print("DOWNLOAD SUMMARY")
    print("=" * 30)
    print(f"Total items found: {download_summary['total']} ({download_summary.get('photos', 0)} photos, {download_summary.get('videos', 0)} videos)")
    print(f"Successfully downloaded: {download_summary['success']}")
    print(f"Failed downloads: {download_summary['failed']}")
    
    if download_summary['success'] > 0:
        print(f"\nMedia saved to date-organized folders under '{args.download_dir}' directory")
    
    if download_summary['failed'] > 0:
        print(f"\nSome downloads failed. Check network connection and try again.")
    
    return 0  # Success exit code

if __name__ == "__main__":
    exit(main())