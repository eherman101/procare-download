#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime
import re

def get_kid_ids(auth_data):
    """
    Get kid IDs for the authenticated parent
    
    Args:
        auth_data: Authentication data from login
    
    Returns:
        list: List of kid dictionaries with id and name
    """
    base_url = auth_data['sites'][0]['base_url']
    kids_url = f"{base_url}/api/web/parent/kids/"
    
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': f'Bearer {auth_data["auth_token"]}',
        'origin': 'https://schools.procareconnect.com',
        'referer': 'https://schools.procareconnect.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(kids_url, headers=headers)
        response.raise_for_status()
        
        kids_data = response.json()
        kids = []
        
        for kid in kids_data.get('kids', []):
            kids.append({
                'id': kid['id'],
                'name': kid['name'],
                'first_name': kid['first_name'],
                'last_name': kid['last_name']
            })
        
        print(f"Found {len(kids)} children: {', '.join([k['name'] for k in kids])}")
        return kids
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching kids: {e}")
        return []

def get_dashboard_photos(auth_data, kid_id=None, date_to=None):
    """
    Get photo activities via API for a specific child
    
    Args:
        auth_data: Authentication data from login
        kid_id: Child ID (if None, will get all children)
        date_to: Date to fetch photos up to (YYYY-MM-DD format)
    
    Returns:
        list: List of photo dictionaries with URLs and metadata
    """
    if date_to is None:
        from datetime import datetime
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    # Get kid IDs if not provided
    if kid_id is None:
        kids = get_kid_ids(auth_data)
        if not kids:
            return []
        kid_id = kids[0]['id']  # Use first child
        print(f"Using child: {kids[0]['name']}")
    
    base_url = auth_data['sites'][0]['base_url']
    activities_url = f"{base_url}/api/web/parent/daily_activities/"
    
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': f'Bearer {auth_data["auth_token"]}',
        'origin': 'https://schools.procareconnect.com',
        'referer': 'https://schools.procareconnect.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
    }
    
    params = {
        'kid_id': kid_id,
        'filters[daily_activity][date_to]': date_to,
        'page': 1
    }
    
    all_photos = []
    page = 1
    
    try:
        while True:
            params['page'] = page
            response = requests.get(activities_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            daily_activities = data.get('daily_activities', [])
            
            if not daily_activities:
                break
            
            photos_this_page = []
            for activity in daily_activities:
                if activity.get('activity_type') == 'photo_activity' and activity.get('activiable'):
                    activiable = activity['activiable']
                    if activiable.get('main_url'):
                        # Extract filename from URL
                        filename = extract_filename_from_url(activiable['main_url'])
                        
                        # Format timestamp
                        activity_time = activity.get('activity_time', '')
                        activity_date = activity.get('activity_date', '')
                        
                        photos_this_page.append({
                            'id': activity['id'],
                            'url': activiable['main_url'],
                            'medium_url': activiable.get('medium_url', ''),
                            'thumb_url': activiable.get('thumb_url', ''),
                            'filename': filename,
                            'date': activity_date,
                            'timestamp': activity_time,
                            'activity_type': 'photo_activity',
                            'caption': activiable.get('caption', ''),
                            'likes': activiable.get('likes_counts', {}),
                            'batch_id': activity.get('batch_id', ''),
                            'staff_name': activity.get('staff_present_name', '')
                        })
            
            all_photos.extend(photos_this_page)
            print(f"Page {page}: Found {len(photos_this_page)} photos")
            
            # Check if there are more pages
            per_page = data.get('per_page', 30)
            if len(daily_activities) < per_page:
                break
            
            page += 1
            
            # Safety limit to prevent infinite loops
            if page > 100:
                print("Warning: Reached page limit of 100")
                break
        
        print(f"Total photos found: {len(all_photos)}")
        return all_photos
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching activities: {e}")
        return []

def extract_filename_from_url(url):
    """Extract a meaningful filename from the photo URL"""
    # Extract the UUID-like part at the end before query parameters
    match = re.search(r'/([a-f0-9-]{36})\.jpg', url)
    if match:
        return f"{match.group(1)}.jpg"
    
    # Fallback: use timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"photo_{timestamp}.jpg"

def download_photo(photo_info, download_dir="photos"):
    """
    Download a single photo with proper headers
    
    Args:
        photo_info: Dictionary with photo URL and metadata
        download_dir: Directory to save photos
    
    Returns:
        bool: True if successful, False otherwise
    """
    os.makedirs(download_dir, exist_ok=True)
    
    headers = {
        'sec-ch-ua-platform': '"Windows"',
        'Referer': 'https://schools.procareconnect.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        'DNT': '1',
        'sec-ch-ua-mobile': '?0'
    }
    
    try:
        response = requests.get(photo_info['url'], headers=headers, stream=True)
        response.raise_for_status()
        
        filepath = os.path.join(download_dir, photo_info['filename'])
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {photo_info['filename']} ({photo_info['date']} {photo_info['timestamp']})")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {photo_info['filename']}: {e}")
        return False
    except IOError as e:
        print(f"Error saving {photo_info['filename']}: {e}")
        return False

def download_all_photos(auth_data, download_dir="photos"):
    """
    Download all photos from the dashboard
    
    Args:
        auth_data: Authentication data from login
        download_dir: Directory to save photos
    
    Returns:
        dict: Summary of download results
    """
    photos = get_dashboard_photos(auth_data)
    
    if not photos:
        return {"success": 0, "failed": 0, "total": 0}
    
    success_count = 0
    failed_count = 0
    
    print(f"\nStarting download of {len(photos)} photos...")
    
    for i, photo in enumerate(photos, 1):
        print(f"Downloading {i}/{len(photos)}: ", end="")
        
        if download_photo(photo, download_dir):
            success_count += 1
        else:
            failed_count += 1
    
    summary = {
        "success": success_count,
        "failed": failed_count, 
        "total": len(photos)
    }
    
    print(f"\nDownload complete!")
    print(f"Successfully downloaded: {success_count}")
    print(f"Failed downloads: {failed_count}")
    print(f"Total photos: {len(photos)}")
    
    return summary

if __name__ == "__main__":
    # Load auth data from file
    try:
        with open('auth_session.json', 'r') as f:
            auth_data = json.load(f)
        
        download_all_photos(auth_data)
        
    except FileNotFoundError:
        print("Error: auth_session.json not found. Please run login.py first.")
    except json.JSONDecodeError:
        print("Error: Invalid auth_session.json file.")