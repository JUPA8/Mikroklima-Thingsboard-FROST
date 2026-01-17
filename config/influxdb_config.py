#!/usr/bin/env python3
"""
InfluxDB Configuration - Get proper token and org
"""

import requests

INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_USERNAME = "admin"
INFLUXDB_PASSWORD = "adminpassword"
INFLUXDB_ORG = "mikroklima"
INFLUXDB_BUCKET = "mikroklima_data"

def get_influxdb_token():
    """Get InfluxDB authentication token"""
    try:
        # Try to authenticate
        auth_url = f"{INFLUXDB_URL}/api/v2/signin"
        response = requests.post(
            auth_url,
            auth=(INFLUXDB_USERNAME, INFLUXDB_PASSWORD)
        )
        
        if response.status_code == 204:
            # Get session cookie
            session_cookie = response.cookies.get('session')
            
            # Get tokens
            tokens_url = f"{INFLUXDB_URL}/api/v2/authorizations"
            headers = {"Cookie": f"session={session_cookie}"}
            token_response = requests.get(tokens_url, headers=headers)
            
            if token_response.status_code == 200:
                tokens = token_response.json().get("authorizations", [])
                if tokens:
                    token = tokens[0]["token"]
                    print(f"✓ InfluxDB Token: {token}")
                    return token
        
        print("⚠ Could not retrieve token via API, using default")
        return "your-influxdb-token-here"
        
    except Exception as e:
        print(f"✗ InfluxDB auth error: {e}")
        return "your-influxdb-token-here"

if __name__ == "__main__":
    print("\n" + "="*70)
    print("INFLUXDB CONFIGURATION")
    print("="*70 + "\n")
    print(f"URL: {INFLUXDB_URL}")
    print(f"Org: {INFLUXDB_ORG}")
    print(f"Bucket: {INFLUXDB_BUCKET}")
    print(f"Username: {INFLUXDB_USERNAME}\n")
    
    token = get_influxdb_token()
    
    print(f"\nAdd this to your complete_data_loader.py:")
    print(f'INFLUXDB_TOKEN = "{token}"')
    print("\n" + "="*70 + "\n")
