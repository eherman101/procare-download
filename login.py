#!/usr/bin/env python3

import requests
import json
import os
from dotenv import load_dotenv

def load_credentials():
    """Load credentials from .env.secrets file"""
    load_dotenv('.env.secrets')
    return {
        'url': os.getenv('PROCARE_URL'),
        'username': os.getenv('PROCARE_USERNAME'), 
        'password': os.getenv('PROCARE_PASSWORD')
    }

def login_to_procare(username, password):
    """
    Login to ProCare Connect and return authentication info
    
    Returns:
        dict: Authentication response containing auth_token and site info
    """
    login_url = "https://online-auth.procareconnect.com/sessions/"
    
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://schools.procareconnect.com',
        'referer': 'https://schools.procareconnect.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
    }
    
    payload = {
        "email": username,
        "password": password,
        "role": "carer",
        "platform": "web"
    }
    
    try:
        response = requests.post(login_url, headers=headers, json=payload)
        response.raise_for_status()
        
        auth_data = response.json()
        
        print("Login successful!")
        print(f"Auth Token: {auth_data['auth_token']}")
        print(f"User ID: {auth_data['user']['id']}")
        print(f"Site: {auth_data['sites'][0]['name']}")
        print(f"Base URL: {auth_data['sites'][0]['base_url']}")
        
        return auth_data
        
    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None

def main():
    """Main function to test login"""
    creds = load_credentials()
    
    if not all(creds.values()):
        print("Error: Missing credentials in .env.secrets file")
        return
    
    auth_data = login_to_procare(creds['username'], creds['password'])
    
    if auth_data:
        # Save auth data for other scripts to use
        with open('auth_session.json', 'w') as f:
            json.dump(auth_data, f, indent=2)
        print("Authentication data saved to auth_session.json")

if __name__ == "__main__":
    main()