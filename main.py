#!/usr/bin/env python3

import os
from login import login_to_procare, load_credentials
from dashboard_scraper import download_all_photos

def main():
    """
    Main script to login to ProCare and download all photos
    """
    print("ProCare Photo Downloader")
    print("=" * 30)
    
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
    
    # Download photos
    print("\nFetching and downloading photos...")
    download_summary = download_all_photos(auth_data)
    
    print("\n" + "=" * 30)
    print("DOWNLOAD SUMMARY")
    print("=" * 30)
    print(f"Total photos found: {download_summary['total']}")
    print(f"Successfully downloaded: {download_summary['success']}")
    print(f"Failed downloads: {download_summary['failed']}")
    
    if download_summary['success'] > 0:
        print(f"\nPhotos saved to 'photos' directory")
    
    if download_summary['failed'] > 0:
        print(f"\nSome downloads failed. Check network connection and try again.")

if __name__ == "__main__":
    main()