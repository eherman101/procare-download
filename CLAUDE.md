# ProCare Photo Downloader

A Python application that automatically downloads photos from ProCare Connect, a childcare management platform. This tool enables parents to bulk download their child's photos from the ProCare system.

## Overview

This project was developed to solve the problem of manually downloading individual photos from the ProCare Connect parent portal. Instead of clicking through hundreds of photos one by one, this tool uses the ProCare API to authenticate as a parent and automatically download all available photos.

## How It Works

### Authentication Flow
1. **Login**: Uses the ProCare authentication endpoint (`https://online-auth.procareconnect.com/sessions/`) with email, password, role ("carer"), and platform ("web")
2. **Get Auth Token**: Receives a Bearer token and site information for API access
3. **Child Discovery**: Fetches child information from `/api/web/parent/kids/` endpoint
4. **Photo Retrieval**: Uses the `/api/web/parent/daily_activities/` API to get paginated photo data

### Technical Implementation
- **API-based**: Uses official ProCare API endpoints (discovered through browser network analysis)
- **Authenticated Requests**: All API calls use Bearer token authentication
- **Paginated Downloads**: Handles multiple pages of photo activities
- **Proper Headers**: Mimics browser requests with correct User-Agent and headers
- **Error Handling**: Graceful handling of network errors and edge cases

## Project Structure

```
procare-download/
├── .env.secrets          # Credentials (email, password, URL)
├── auth_session.json     # Cached authentication data
├── login.py             # Authentication and session management
├── dashboard_scraper.py # API-based photo discovery and download
├── main.py              # Main orchestration script
├── photos/              # Downloaded photos directory
└── venv/                # Python virtual environment
```

## Key Files

### `login.py`
- Handles ProCare authentication
- Loads credentials from `.env.secrets`
- Returns authentication data including Bearer token and site info
- Saves session data for reuse

### `dashboard_scraper.py`
- **`get_kid_ids()`**: Fetches child information from parent account
- **`get_dashboard_photos()`**: Uses API to get all photo activities (paginated)
- **`download_photo()`**: Downloads individual photos with proper headers
- **`download_all_photos()`**: Orchestrates the complete download process

### `main.py`
- Main entry point that coordinates the entire workflow
- Provides progress reporting and download summaries

## Development Process

This project was developed by reverse-engineering the ProCare Connect web application through browser network analysis:

1. **Manual Login Analysis**: Examined the login form and identified required fields
2. **Network Traffic Inspection**: Used Chrome DevTools to capture API requests
3. **Authentication Flow**: Discovered the JWT Bearer token system
4. **API Endpoint Discovery**: Found the `/api/web/parent/kids/` and `/api/web/parent/daily_activities/` endpoints
5. **Request Headers**: Identified required headers for photo downloads
6. **Pagination Handling**: Implemented support for multiple pages of results

## Features

- ✅ **Automated Authentication**: Logs in using stored credentials
- ✅ **Child Discovery**: Automatically finds children associated with parent account
- ✅ **Bulk Photo Download**: Downloads all available photos in batch
- ✅ **Progress Tracking**: Shows download progress and counts
- ✅ **Unique Filenames**: Uses UUID-based filenames to prevent conflicts
- ✅ **Metadata Preservation**: Includes date, timestamp, and activity information
- ✅ **Error Recovery**: Handles network errors and continues downloading
- ✅ **Pagination Support**: Processes multiple pages of photo activities

## Setup and Usage

### Prerequisites
- Python 3.7+
- Virtual environment support
- Network access to ProCare Connect APIs

### Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install requests python-dotenv

# Set up credentials
echo "PROCARE_URL=https://schools.procareconnect.com/login" > .env.secrets
echo "PROCARE_USERNAME=your.email@example.com" >> .env.secrets
echo "PROCARE_PASSWORD=your_password" >> .env.secrets
```

### Running the Downloader
```bash
source venv/bin/activate
python main.py
```

## Results

The application successfully:
- Authenticated with ProCare Connect
- Discovered 1 child account (Herman, Astrid)
- Found 2,667 total photos across 100+ pages
- Downloaded photos with proper authentication headers
- Saved photos to local `photos/` directory with UUID filenames

## Security Considerations

- Credentials are stored in `.env.secrets` (not committed to git)
- Uses HTTPS for all API communications
- Bearer tokens are properly handled and not logged
- No sensitive information is exposed in output logs

## Technical Notes

### API Endpoints Discovered
- **Authentication**: `POST https://online-auth.procareconnect.com/sessions/`
- **Child Info**: `GET https://api-school.procareconnect.com/api/web/parent/kids/`
- **Activities**: `GET https://api-school.procareconnect.com/api/web/parent/daily_activities/`
- **Photo Downloads**: Direct HTTPS requests to `private.kinderlime.com` CDN

### Request Headers Required
- `Authorization: Bearer {token}` for API calls
- `Referer: https://schools.procareconnect.com/` for photo downloads
- Proper User-Agent string to mimic browser requests

## Future Enhancements

Potential improvements for this project:
- Date range filtering for selective downloads
- Resume capability for interrupted downloads
- Photo organization by date/activity type
- Support for video downloads
- Multiple child support
- GUI interface for non-technical users

## Development Environment

This project was developed using:
- **Claude Code**: AI-assisted development environment
- **Python 3.11**: Core programming language
- **Browser Network Analysis**: For API discovery
- **Git**: Version control
- **GitHub CLI**: Repository management

---

*This project demonstrates API reverse engineering, authentication handling, and bulk data retrieval from a third-party service.*