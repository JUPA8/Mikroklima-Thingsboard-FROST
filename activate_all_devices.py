#!/usr/bin/env python3
"""
Activate All ThingsBoard Devices
Generates and sends data to all devices including demo sources
"""

import requests
import json
import time
import random
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "mikroklima-super-secret-token"
INFLUXDB_ORG = "mikroklima"
INFLUXDB_BUCKET = "mikroklima_data"
FROST_URL = "http://localhost:8091/FROST-Server/v1.1"
TB_URL = "http://localhost:8080"

# Load ThingsBoard credentials
with open('config/thingsboard_credentials.json', 'r') as f:
    TB_DEVICE_TOKENS = json.load(f)

# Device configurations with simulated data
DEVICES = {
    'DWD_01975': {
        'name': 'DWD Station Hamburg',
        'location': {'lat': 53.6333, 'lon': 10.0000},
        'sensors': ['Temperature', 'Humidity', 'Pressure', 'Wind Speed']
    },
    'Hamburg_Luftmessnetz': {
        'name': 'Hamburg Air Quality Network',
        'location': {'lat': 53.5511, 'lon': 9.9937},
        'sensors': ['PM10', 'PM2.5', 'NO2', 'O3']
    },
    'UDP_Osnabrueck': {
        'name': 'UDP Osnabrück Microclimate',
        'location': {'lat': 52.2799, 'lon': 8.0472},
        'sensors': ['Temperature', 'Humidity', 'Soil Moisture']
    },
    'Tunisia': {
        'name': 'Tunisia Weather Station',
        'location': {'lat': 36.8065, 'lon': 10.1815},
        'sensors': ['Temperature', 'Humidity', 'Wind Speed']
    },
    'Open-Meteo Alexandria': {
        'name': 'Open-Meteo Alexandria',
        'location': {'lat': 31.2001, 'lon': 29.9187},
        'sensors': ['Temperature', 'Humidity', 'Pressure']
    },
    'Open-Meteo Hurghada': {
        'name': 'Open-Meteo Hurghada',
        'location': {'lat': 27.2579, 'lon': 33.8116},
        'sensors': ['Temperature', 'Humidity', 'Pressure']
    }
}

def generate_sensor_value(sensor_type, location_name):
    """Generate realistic sensor values based on type and location"""

    # Base temperatures by location
    temp_base = {
        'Hamburg': 5,
        'Osnabrück': 6,
        'Tunisia': 18,
        'Alexandria': 20,
        'Hurghada': 25
    }

    base_temp = 15  # default
    for loc in temp_base:
        if loc.lower() in location_name.lower():
            base_temp = temp_base[loc]
            break

    if sensor_type == 'Temperature':
        return round(base_temp + random.uniform(-3, 3), 2)
    elif sensor_type == 'Humidity':
        return round(random.uniform(40, 80), 2)
    elif sensor_type == 'Pressure':
        return round(random.uniform(1010, 1025), 2)
    elif sensor_type == 'Wind Speed':
        return round(random.uniform(2, 15), 2)
    elif sensor_type == 'PM10':
        return round(random.uniform(10, 30), 2)
    elif sensor_type == 'PM2.5':
        return round(random.uniform(5, 15), 2)
    elif sensor_type == 'NO2':
        return round(random.uniform(15, 45), 2)
    elif sensor_type == 'O3':
        return round(random.uniform(30, 70), 2)
    elif sensor_type == 'Soil Moisture':
        return round(random.uniform(20, 60), 2)
    else:
        return round(random.uniform(10, 30), 2)

def send_to_thingsboard(device_key, telemetry):
    """Send data to ThingsBoard"""
    if device_key not in TB_DEVICE_TOKENS:
        print(f"  ⚠ No token for {device_key}")
        return False

    access_token = TB_DEVICE_TOKENS[device_key]
    url = f"{TB_URL}/api/v1/{access_token}/telemetry"

    try:
        response = requests.post(url, json=telemetry, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"  ✗ ThingsBoard error: {e}")
        return False

def send_to_influxdb(source, location, measurements):
    """Send data to InfluxDB"""
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        write_api = client.write_api(write_options=SYNCHRONOUS)

        for measurement in measurements:
            point = Point("microclimate") \
                .tag("source", source) \
                .tag("sensor_type", measurement['type']) \
                .tag("location", f"{location['lat']},{location['lon']}") \
                .field("value", measurement['value']) \
                .time(datetime.now(timezone.utc))

            write_api.write(bucket=INFLUXDB_BUCKET, record=point)

        client.close()
        return True
    except Exception as e:
        print(f"  ✗ InfluxDB error: {e}")
        return False

def send_to_frost(source, location, measurements):
    """Send data to FROST Server"""
    try:
        # Create Thing if not exists
        thing_name = source
        thing_data = {
            "name": thing_name,
            "description": f"Auto-created Thing for {source}",
            "properties": {"source": "automated"}
        }

        # Try to create or get Thing
        response = requests.post(f"{FROST_URL}/Things", json=thing_data, timeout=5)

        if response.status_code == 201:
            thing_id = response.json()['@iot.id']
        else:
            # Thing might exist, try to get it
            search_response = requests.get(
                f"{FROST_URL}/Things?$filter=name eq '{thing_name}'",
                timeout=5
            )
            if search_response.status_code == 200:
                things = search_response.json().get('value', [])
                if things:
                    thing_id = things[0]['@iot.id']
                else:
                    return False
            else:
                return False

        # Create Location
        location_data = {
            "name": f"{source} Location",
            "description": f"Location of {source}",
            "encodingType": "application/vnd.geo+json",
            "location": {
                "type": "Point",
                "coordinates": [location['lon'], location['lat']]
            }
        }
        requests.post(f"{FROST_URL}/Things({thing_id})/Locations", json=location_data, timeout=5)

        return True
    except Exception as e:
        print(f"  ✗ FROST error: {e}")
        return False

def main():
    print("=" * 70)
    print("ACTIVATING ALL THINGSBOARD DEVICES")
    print("=" * 70)
    print()

    for device_key, config in DEVICES.items():
        print(f"📡 {config['name']}")
        print(f"  Location: {config['location']['lat']:.4f}°N, {config['location']['lon']:.4f}°E")

        # Generate measurements
        measurements = []
        telemetry = {}

        for sensor_type in config['sensors']:
            value = generate_sensor_value(sensor_type, config['name'])
            measurements.append({
                'type': sensor_type,
                'value': value
            })
            telemetry[sensor_type.lower().replace(' ', '_')] = value
            print(f"  - {sensor_type}: {value}")

        print(f"\n  Pushing to platforms:")

        # Send to ThingsBoard
        if send_to_thingsboard(device_key, telemetry):
            print(f"    ✓ ThingsBoard")

        # Send to InfluxDB
        if send_to_influxdb(config['name'], config['location'], measurements):
            print(f"    ✓ InfluxDB")

        # Send to FROST
        if send_to_frost(config['name'], config['location'], measurements):
            print(f"    ✓ FROST")

        print()
        time.sleep(1)

    print("=" * 70)
    print("✓ All devices activated!")
    print("=" * 70)
    print("\nCheck your platforms:")
    print("- ThingsBoard: http://localhost:8080")
    print("- InfluxDB: http://localhost:8086")
    print("- FROST Server: http://localhost:8091/FROST-Server/v1.1")

if __name__ == "__main__":
    main()
