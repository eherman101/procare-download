#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime
import re
import time
from dateutil import parser

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

def get_dashboard_photos(auth_data, kid_id=None, date_from=None, date_to=None):
    """
    Get photo activities via API for a specific child
    
    Args:
        auth_data: Authentication data from login
        kid_id: Child ID (if None, will get all children)
        date_from: Start date to fetch photos from (YYYY-MM-DD format)
        date_to: End date to fetch photos up to (YYYY-MM-DD format)
    
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
        'page': 1
    }
    
    # Add date filters if provided
    if date_to:
        params['filters[daily_activity][date_to]'] = date_to
    if date_from:
        params['filters[daily_activity][date_from]'] = date_from
    
    all_photos = []
    page = 1
    
    try:
        while True:
            params['page'] = page
            
            # Add small delay between API calls to be respectful
            if page > 1:
                time.sleep(1)  # 1 second delay between pages
            
            response = requests.get(activities_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            daily_activities = data.get('daily_activities', [])
            
            if not daily_activities:
                break
            
            media_this_page = []
            for activity in daily_activities:
                if activity.get('activity_type') in ['photo_activity', 'video_activity'] and activity.get('activiable'):
                    activiable = activity['activiable']
                    
                    # Determine if this is a video or photo
                    is_video = activiable.get('is_video', False)
                    
                    # Get the appropriate URL
                    if is_video and activiable.get('video_file_url'):
                        media_url = activiable['video_file_url']
                        file_extension = 'mp4'  # Most videos are mp4, but we could detect from URL
                    elif activiable.get('main_url'):
                        media_url = activiable['main_url']
                        file_extension = 'jpg'
                    else:
                        continue  # Skip if no URL available
                        
                    # Extract filename from URL
                    filename = extract_filename_from_url(media_url, file_extension)
                    
                    # Parse date for folder organization
                    activity_date_raw = activiable.get('date', '') or activity.get('activity_date', '')
                    folder_date = parse_date_for_folder(activity_date_raw)
                    
                    # Format timestamp
                    activity_time = activity.get('activity_time', '')
                    activity_date = activity.get('activity_date', '')
                    
                    media_this_page.append({
                        'id': activity['id'],
                        'url': media_url,
                        'medium_url': activiable.get('medium_url', ''),
                        'thumb_url': activiable.get('thumb_url', ''),
                        'filename': filename,
                        'folder_date': folder_date,
                        'date': activity_date,
                        'timestamp': activity_time,
                        'activity_type': activity.get('activity_type', ''),
                        'is_video': is_video,
                        'file_extension': file_extension,
                        'caption': activiable.get('caption', ''),
                        'likes': activiable.get('likes_counts', {}),
                        'batch_id': activity.get('batch_id', ''),
                        'staff_name': activity.get('staff_present_name', '')
                    })
            
            all_photos.extend(media_this_page)
            videos_count = len([m for m in media_this_page if m['is_video']])
            photos_count = len(media_this_page) - videos_count
            print(f"Page {page}: Found {photos_count} photos, {videos_count} videos")
            
            # Check if there are more pages
            per_page = data.get('per_page', 30)
            if len(daily_activities) < per_page:
                break
            
            page += 1
            
            # Safety limit to prevent infinite loops
            if page > 100:
                print("Warning: Reached page limit of 100")
                break
        
        total_videos = len([m for m in all_photos if m['is_video']])
        total_photos = len(all_photos) - total_videos
        print(f"Total media found: {total_photos} photos, {total_videos} videos")
        return all_photos
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching activities: {e}")
        return []

def parse_date_for_folder(date_string):
    """
    Parse date string and return folder-friendly date format (YYYY-MM-DD)
    """
    if not date_string:
        return datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Parse the ISO date string (handles timezone)
        parsed_date = parser.parse(date_string)
        # Convert to EST if needed (though the date part should be the same)
        return parsed_date.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        # Fallback to current date if parsing fails
        return datetime.now().strftime('%Y-%m-%d')

def extract_filename_from_url(url, file_extension='jpg'):
    """Extract a meaningful filename from the media URL"""
    # Extract the UUID-like part at the end before query parameters
    if file_extension == 'mp4':
        # For videos, look for .mp4 or similar
        match = re.search(r'/([a-f0-9-]{36})\.(mp4|mov|avi)', url)
        if match:
            actual_ext = match.group(2)
            return f"{match.group(1)}.{actual_ext}"
    else:
        # For photos
        match = re.search(r'/([a-f0-9-]{36})\.jpg', url)
        if match:
            return f"{match.group(1)}.jpg"
    
    # Fallback: use timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"media_{timestamp}.{file_extension}"

def download_media(media_info, base_download_dir="downloads", add_delay=True):
    """
    Download a single photo or video with proper headers and organize by date
    
    Args:
        media_info: Dictionary with media URL and metadata
        base_download_dir: Base directory to save media
        add_delay: Whether to add a delay after download (for rate limiting)
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Create date-based folder structure
    folder_date = media_info.get('folder_date', datetime.now().strftime('%Y-%m-%d'))
    download_dir = os.path.join(base_download_dir, folder_date)
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
        response = requests.get(media_info['url'], headers=headers, stream=True)
        response.raise_for_status()
        
        filepath = os.path.join(download_dir, media_info['filename'])
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        media_type = "video" if media_info['is_video'] else "photo"
        print(f"Downloaded {media_type}: {media_info['filename']} to {folder_date}/ ({media_info['date']})")
        
        # Add small delay after each download to be respectful to the server
        if add_delay:
            time.sleep(0.5)  # 500ms delay between downloads
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {media_info['filename']}: {e}")
        return False
    except IOError as e:
        print(f"Error saving {media_info['filename']}: {e}")
        return False

def download_all_media(auth_data, download_dir="downloads", date_from=None, date_to=None):
    """
    Download all photos and videos from the dashboard
    
    Args:
        auth_data: Authentication data from login
        download_dir: Base directory to save media (will create date subfolders)
        date_from: Start date for filtering (YYYY-MM-DD format)
        date_to: End date for filtering (YYYY-MM-DD format)
    
    Returns:
        dict: Summary of download results
    """
    media_items = get_dashboard_photos(auth_data, date_from=date_from, date_to=date_to)  # This now returns photos AND videos
    
    if not media_items:
        return {"success": 0, "failed": 0, "total": 0, "photos": 0, "videos": 0}
    
    success_count = 0
    failed_count = 0
    photos_count = 0
    videos_count = 0
    
    # Count media types
    for item in media_items:
        if item['is_video']:
            videos_count += 1
        else:
            photos_count += 1
    
    date_range_msg = ""
    if date_from or date_to:
        date_range_msg = f" from {date_from or 'beginning'} to {date_to or 'now'}"
    
    print(f"\nStarting download of {len(media_items)} items ({photos_count} photos, {videos_count} videos){date_range_msg}...")
    
    for i, media_item in enumerate(media_items, 1):
        media_type = "video" if media_item['is_video'] else "photo"
        print(f"Downloading {i}/{len(media_items)} ({media_type}): ", end="")
        
        # Take a 2-minute break after every 100 downloads
        if i > 1 and (i - 1) % 100 == 0:
            print(f"\n🔄 Taking a 2-minute break after {i-1} downloads to avoid rate limiting...")
            time.sleep(120)  # 2 minutes = 120 seconds
            print("✅ Break complete, resuming downloads...")
        
        if download_media(media_item, download_dir):
            success_count += 1
        else:
            failed_count += 1
    
    summary = {
        "success": success_count,
        "failed": failed_count, 
        "total": len(media_items),
        "photos": photos_count,
        "videos": videos_count
    }
    
    print(f"\nDownload complete!")
    print(f"Successfully downloaded: {success_count}")
    print(f"Failed downloads: {failed_count}")
    print(f"Total items: {len(media_items)} ({photos_count} photos, {videos_count} videos)")
    print(f"Files organized in date folders under '{download_dir}/'")
    
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