#!/usr/bin/env python3
"""
Thingsboard Device Setup Script
Creates devices and access tokens for the Mikroklima Hamburg project
"""

import requests
import json
import sys

# Thingsboard configuration
TB_HOST = "http://localhost:8080"
TB_USERNAME = "tenant@thingsboard.org"
TB_PASSWORD = "tenant"

# Device definitions
DEVICES = [
    {
        "name": "OpenSenseMap_5df93d3b39652b001b8cd9d2",
        "label": "OpenSenseMap Hamburg",
        "type": "weather_station"
    },
    {
        "name": "DWD_01975",
        "label": "DWD Station 01975 Hamburg",
        "type": "weather_station"
    },
    {
        "name": "Hamburg_Luftmessnetz",
        "label": "Hamburg Air Quality Network",
        "type": "air_quality"
    },
    {
        "name": "UDP_Osnabrueck",
        "label": "UDP Osnabrück Microclimate",
        "type": "microclimate"
    },
    {
        "name": "Tunisia",
        "label": "Tunisia Weather Station",
        "type": "weather_station"
    },
    {
        "name": "Egypt",
        "label": "Egypt Weather Station",
        "type": "weather_station"
    }
]


def get_auth_token():
    """Authenticate and get JWT token"""
    print("🔐 Authenticating with Thingsboard...")
    
    url = f"{TB_HOST}/api/auth/login"
    payload = {
        "username": TB_USERNAME,
        "password": TB_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        token = response.json()["token"]
        print("✓ Authentication successful")
        return token
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        sys.exit(1)


def create_device(token, device_info):
    """Create a device in Thingsboard"""
    url = f"{TB_HOST}/api/device"
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {token}"
    }
    
    payload = {
        "name": device_info["name"],
        "label": device_info["label"],
        "type": device_info["type"]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        device = response.json()
        print(f"✓ Created device: {device_info['label']}")
        return device
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print(f"⚠ Device already exists: {device_info['label']}")
            # Get existing device
            search_url = f"{TB_HOST}/api/tenant/devices?deviceName={device_info['name']}"
            response = requests.get(search_url, headers=headers)
            return response.json()
        else:
            print(f"✗ Failed to create device {device_info['label']}: {e}")
            return None


def get_device_credentials(token, device_id):
    """Get device access token"""
    url = f"{TB_HOST}/api/device/{device_id}/credentials"
    headers = {
        "X-Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        credentials = response.json()
        return credentials.get("credentialsId")
    except Exception as e:
        print(f"✗ Failed to get credentials: {e}")
        return None


def main():
    print("\n" + "="*70)
    print("THINGSBOARD DEVICE SETUP")
    print("Mikroklima Hamburg Project")
    print("="*70 + "\n")
    
    # Authenticate
    token = get_auth_token()
    
    # Create devices and collect credentials
    credentials_map = {}
    
    print("\n📱 Creating devices...\n")
    for device_info in DEVICES:
        device = create_device(token, device_info)
        if device:
            device_id = device["id"]["id"]
            access_token = get_device_credentials(token, device_id)
            if access_token:
                credentials_map[device_info["name"]] = access_token
                print(f"   Token: {access_token[:20]}...")
    
    # Save credentials to file
    credentials_file = "thingsboard_credentials.json"
    with open(credentials_file, 'w') as f:
        json.dump(credentials_map, f, indent=2)
    
    print(f"\n✓ Credentials saved to {credentials_file}")
    print("\n" + "="*70)
    print("✓ Setup complete!")
    print("="*70)
    print(f"\nAccess Thingsboard at: {TB_HOST}")
    print(f"Username: {TB_USERNAME}")
    print(f"Password: {TB_PASSWORD}\n")


if __name__ == "__main__":
    main()
