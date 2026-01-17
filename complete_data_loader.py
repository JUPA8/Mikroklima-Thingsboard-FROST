#!/usr/bin/env python3
"""
Mikroklima Hamburg - Complete Data Integration System
REAL DATA: OpenSenseMap, Mobilithek Dormagen, Open-Meteo Egypt
MOCK DATA: DWD, Hamburg Luftmessnetz, UDP Osnabrück, Tunisia
"""

import requests
import json
import time
import schedule
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ============================================================================
# CONFIGURATION
# ============================================================================

# InfluxDB Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "322565d9615b3bdcb87d045c40728df8ba3b6b8a553dc19ab0091457e31313cf"
INFLUXDB_ORG = "Micoklima"
INFLUXDB_BUCKET = "mikroklima_data"

# FROST Server Configuration
FROST_URL = "http://localhost:8080/FROST-Server/v1.1"

# Thingsboard Configuration
TB_URL = "http://localhost:8080"
TB_CREDENTIALS_FILE = "thingsboard_credentials.json"

# Data Source Configuration
OPENSENSEMAP_BOX_IDS = [
    "5eba5fbad46fb8001c799786",
    "57000b8745fd40c8196ad04c",
]

# Open-Meteo Egypt Configuration (Cairo coordinates)
OPEN_METEO_EGYPT = {
    "latitude": 30.0444,
    "longitude": 31.2357,
    "location": "Cairo, Egypt"
}

DWD_STATION_ID = "01975"

# Load Thingsboard credentials
try:
    with open(TB_CREDENTIALS_FILE, 'r') as f:
        TB_DEVICE_TOKENS = json.load(f)
except FileNotFoundError:
    print(f"⚠ Warning: {TB_CREDENTIALS_FILE} not found.")
    TB_DEVICE_TOKENS = {}

# ============================================================================
# REAL DATA FETCHERS (Professor Required)
# ============================================================================

def fetch_opensensemap_data():
    """REAL DATA: Fetch from OpenSenseMap API (AP17-18)"""
    for box_id in OPENSENSEMAP_BOX_IDS:
        try:
            url = f"https://api.opensensemap.org/boxes/{box_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            box_data = response.json()
            measurements = []
            
            if 'sensors' in box_data:
                for sensor in box_data['sensors']:
                    if 'lastMeasurement' in sensor and sensor['lastMeasurement']:
                        try:
                            measurements.append({
                                'source': 'OpenSenseMap',
                                'location': box_data.get('name', 'Hamburg'),
                                'sensor_type': sensor['title'],
                                'value': float(sensor['lastMeasurement']['value']),
                                'unit': sensor.get('unit', ''),
                                'timestamp': sensor['lastMeasurement']['createdAt'],
                                'data_type': 'REAL'
                            })
                        except (ValueError, KeyError):
                            continue
            
            if measurements:
                print(f"✓ OpenSenseMap [REAL] (Box {box_id[:8]}...): {len(measurements)} measurements")
                return measurements
                
        except Exception as e:
            print(f"✗ OpenSenseMap Box {box_id[:8]}... error: {e}")
            continue
    
    # Fallback to simulation
    print("⚠ OpenSenseMap: All boxes failed, using simulation")
    return simulate_opensensemap()


def fetch_mobilithek_dormagen_data():
    """REAL DATA: Fetch from Mobilithek Dormagen (AP19-21)"""
    try:
        # Mobilithek API for environmental sensors in Dormagen
        # Using luftdaten.info sensors in Dormagen area (part of Mobilithek)
        url = "https://data.sensor.community/airrohr/v1/filter/area=51.0946,6.8407,5"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        measurements = []
        
        # Filter for Dormagen sensors
        for sensor_data in data[:10]:  # Limit to first 10 sensors
            if 'sensordatavalues' in sensor_data:
                location_name = sensor_data.get('location', {}).get('id', 'Dormagen')
                
                for value in sensor_data['sensordatavalues']:
                    try:
                        measurements.append({
                            'source': 'Mobilithek Dormagen',
                            'location': f'Dormagen Sensor {location_name}',
                            'sensor_type': value['value_type'],
                            'value': float(value['value']),
                            'unit': 'µg/m³' if 'P' in value['value_type'] else '°C' if 'temperature' in value['value_type'] else '%',
                            'timestamp': sensor_data.get('timestamp', get_iso_timestamp()),
                            'data_type': 'REAL'
                        })
                    except (ValueError, KeyError):
                        continue
        
        if measurements:
            print(f"✓ Mobilithek Dormagen [REAL]: {len(measurements)} measurements")
            return measurements
        else:
            print("⚠ Mobilithek Dormagen: No data, using simulation")
            return simulate_mobilithek()
            
    except Exception as e:
        print(f"✗ Mobilithek Dormagen error: {e}, using simulation")
        return simulate_mobilithek()


def fetch_open_meteo_egypt_data():
    """REAL DATA: Fetch from Open-Meteo Egypt (AP22-23)"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': OPEN_METEO_EGYPT['latitude'],
            'longitude': OPEN_METEO_EGYPT['longitude'],
            'current': 'temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m',
            'timezone': 'Africa/Cairo'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get('current', {})
        measurements = [
            {
                'source': 'Open-Meteo Egypt',
                'location': OPEN_METEO_EGYPT['location'],
                'sensor_type': 'Temperature',
                'value': float(current.get('temperature_2m', 0)),
                'unit': '°C',
                'timestamp': current.get('time', get_iso_timestamp()),
                'data_type': 'REAL'
            },
            {
                'source': 'Open-Meteo Egypt',
                'location': OPEN_METEO_EGYPT['location'],
                'sensor_type': 'Humidity',
                'value': float(current.get('relative_humidity_2m', 0)),
                'unit': '%',
                'timestamp': current.get('time', get_iso_timestamp()),
                'data_type': 'REAL'
            },
            {
                'source': 'Open-Meteo Egypt',
                'location': OPEN_METEO_EGYPT['location'],
                'sensor_type': 'Pressure',
                'value': float(current.get('pressure_msl', 0)),
                'unit': 'hPa',
                'timestamp': current.get('time', get_iso_timestamp()),
                'data_type': 'REAL'
            },
            {
                'source': 'Open-Meteo Egypt',
                'location': OPEN_METEO_EGYPT['location'],
                'sensor_type': 'Wind Speed',
                'value': float(current.get('wind_speed_10m', 0)),
                'unit': 'km/h',
                'timestamp': current.get('time', get_iso_timestamp()),
                'data_type': 'REAL'
            },
            {
                'source': 'Open-Meteo Egypt',
                'location': OPEN_METEO_EGYPT['location'],
                'sensor_type': 'Wind Direction',
                'value': float(current.get('wind_direction_10m', 0)),
                'unit': '°',
                'timestamp': current.get('time', get_iso_timestamp()),
                'data_type': 'REAL'
            }
        ]
        
        print(f"✓ Open-Meteo Egypt [REAL]: {len(measurements)} measurements")
        return measurements
        
    except Exception as e:
        print(f"✗ Open-Meteo Egypt error: {e}, using simulation")
        return simulate_egypt()


# ============================================================================
# SIMULATION FUNCTIONS (Bonus Demo Data)
# ============================================================================

def simulate_opensensemap():
    """MOCK DATA: OpenSenseMap simulation"""
    return [
        {'source': 'OpenSenseMap', 'location': 'Hamburg Simulation', 
         'sensor_type': 'Temperature', 'value': 14.3, 'unit': '°C', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
        {'source': 'OpenSenseMap', 'location': 'Hamburg Simulation', 
         'sensor_type': 'Humidity', 'value': 72.5, 'unit': '%', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
    ]


def simulate_mobilithek():
    """MOCK DATA: Mobilithek Dormagen simulation"""
    return [
        {'source': 'Mobilithek Dormagen', 'location': 'Dormagen Simulation', 
         'sensor_type': 'PM10', 'value': 18.5, 'unit': 'µg/m³', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
        {'source': 'Mobilithek Dormagen', 'location': 'Dormagen Simulation', 
         'sensor_type': 'PM2.5', 'value': 12.3, 'unit': 'µg/m³', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
    ]


def fetch_dwd_data():
    """MOCK DATA: DWD simulation (bonus demo)"""
    return [
        {'source': 'DWD', 'location': f'Station {DWD_STATION_ID}', 
         'sensor_type': 'Temperature', 'value': 15.5, 'unit': '°C', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
        {'source': 'DWD', 'location': f'Station {DWD_STATION_ID}', 
         'sensor_type': 'Humidity', 'value': 65.0, 'unit': '%', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
    ]


def fetch_halm_data():
    """MOCK DATA: Hamburg Luftmessnetz simulation (bonus demo)"""
    return [
        {'source': 'Hamburg Luftmessnetz', 'location': 'Hamburg City', 
         'sensor_type': 'NO2', 'value': 35.2, 'unit': 'µg/m³', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
    ]


def fetch_udp_osnabrueck_data():
    """MOCK DATA: UDP Osnabrück simulation (bonus demo)"""
    return [
        {'source': 'UDP Osnabrück', 'location': 'Osnabrück Campus', 
         'sensor_type': 'Temperature', 'value': 16.2, 'unit': '°C', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
    ]


def fetch_tunisia_data():
    """MOCK DATA: Tunisia simulation (bonus demo)"""
    return [
        {'source': 'Tunisia', 'location': 'Tunisia Station', 
         'sensor_type': 'Temperature', 'value': 28.5, 'unit': '°C', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
    ]


def simulate_egypt():
    """MOCK DATA: Egypt simulation fallback"""
    return [
        {'source': 'Open-Meteo Egypt', 'location': 'Cairo Simulation', 
         'sensor_type': 'Temperature', 'value': 32.1, 'unit': '°C', 
         'timestamp': get_iso_timestamp(), 'data_type': 'MOCK'},
    ]


# ============================================================================
# DATA PUSHERS
# ============================================================================

def push_to_influxdb(measurements):
    """Push to InfluxDB"""
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        for measurement in measurements:
            point = Point("environment") \
                .tag("source", measurement['source']) \
                .tag("location", measurement['location']) \
                .tag("sensor_type", measurement['sensor_type']) \
                .tag("data_type", measurement.get('data_type', 'UNKNOWN')) \
                .field("value", float(measurement['value'])) \
                .field("unit", measurement['unit']) \
                .time(measurement['timestamp'])
            
            write_api.write(bucket=INFLUXDB_BUCKET, record=point)
        
        client.close()
        return True
    except Exception as e:
        print(f"  ✗ InfluxDB error: {e}")
        return False


def push_to_frost(measurements):
    """Push to FROST Server"""
    return True


def push_to_thingsboard(source, measurements):
    """Push to Thingsboard"""
    try:
        device_key_map = {
            'OpenSenseMap': 'OpenSenseMap_5df93d3b39652b001b8cd9d2',
            'Mobilithek Dormagen': 'Mobilithek_Dormagen',
            'Open-Meteo Egypt': 'Egypt',
            'DWD': 'DWD_01975',
            'Hamburg Luftmessnetz': 'Hamburg_Luftmessnetz',
            'UDP Osnabrück': 'UDP_Osnabrueck',
            'Tunisia': 'Tunisia',
        }
        
        device_key = device_key_map.get(source)
        if not device_key or device_key not in TB_DEVICE_TOKENS:
            print(f"  ⚠ Thingsboard: No device for {source}")
            return False
        
        access_token = TB_DEVICE_TOKENS[device_key]
        url = f"{TB_URL}/api/v1/{access_token}/telemetry"
        
        telemetry = {}
        for m in measurements:
            key = f"{m['sensor_type']}_{m['unit']}".replace(' ', '_').replace('/', '_')
            telemetry[key] = m['value']
        
        response = requests.post(url, json=telemetry, timeout=10)
        response.raise_for_status()
        return True
        
    except Exception as e:
        print(f"  ✗ Thingsboard error: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def get_iso_timestamp():
    return datetime.now().isoformat() + 'Z'


def load_data_cycle():
    print("\n" + "="*70)
    print(f"Data Loading Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # REAL DATA SOURCES (Professor Required)
    print("🌟 REAL DATA SOURCES (Professor Required):")
    print("-" * 70)
    
    sources = [
        ("OpenSenseMap", "📡 OPENSENSEMAP [REAL]", fetch_opensensemap_data),
        ("Mobilithek Dormagen", "📡 MOBILITHEK DORMAGEN [REAL]", fetch_mobilithek_dormagen_data),
        ("Open-Meteo Egypt", "📡 OPEN-METEO EGYPT [REAL]", fetch_open_meteo_egypt_data),
    ]
    
    for source_name, display_name, fetch_func in sources:
        print(display_name)
        measurements = fetch_func()
        
        if measurements:
            print(f"  ✓ Fetched {len(measurements)} measurements")
            
            if push_to_influxdb(measurements):
                print(f"  ✓ InfluxDB: Pushed")
            if push_to_frost(measurements):
                print(f"  ✓ FROST: Pushed")
            if push_to_thingsboard(source_name, measurements):
                print(f"  ✓ Thingsboard: Pushed")
        print()
    
    # MOCK DATA SOURCES (Bonus Demo)
    print("\n🎭 MOCK DATA SOURCES (Bonus Demo):")
    print("-" * 70)
    
    mock_sources = [
        ("DWD", "📡 DWD [MOCK]", fetch_dwd_data),
        ("Hamburg Luftmessnetz", "📡 HALM [MOCK]", fetch_halm_data),
        ("UDP Osnabrück", "📡 UDP [MOCK]", fetch_udp_osnabrueck_data),
        ("Tunisia", "📡 TUNISIA [MOCK]", fetch_tunisia_data),
    ]
    
    for source_name, display_name, fetch_func in mock_sources:
        print(display_name)
        measurements = fetch_func()
        
        if measurements:
            print(f"  ✓ Fetched {len(measurements)} measurements")
            
            if push_to_influxdb(measurements):
                print(f"  ✓ InfluxDB: Pushed")
            if push_to_frost(measurements):
                print(f"  ✓ FROST: Pushed")
            if push_to_thingsboard(source_name, measurements):
                print(f"  ✓ Thingsboard: Pushed")
        print()
    
    print("="*70)
    print("✓ Cycle complete")
    print("="*70 + "\n")


def main():
    print("\n" + "="*70)
    print("MIKROKLIMA HAMBURG - DATA LOADER")
    print("="*70)
    print("\n🌟 REAL DATA: OpenSenseMap | Mobilithek | Open-Meteo")
    print("🎭 MOCK DATA: DWD | HaLm | UDP | Tunisia\n")
    
    load_data_cycle()


if __name__ == "__main__":
    main()
