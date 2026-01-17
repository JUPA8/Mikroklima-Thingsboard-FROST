#!/usr/bin/env python3
"""
Download Historical Data
- Mobilithek Dormagen (sensor.community) - Last 7 days
- Open-Meteo Egypt (Cairo) - Last 7 days
Saves to data/historical/ folder
"""

import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import time

# Create data directory
os.makedirs('data/historical', exist_ok=True)

print("\n" + "="*80)
print("HISTORICAL DATA DOWNLOAD")
print("="*80 + "\n")

# =============================================================================
# 1. MOBILITHEK DORMAGEN (sensor.community)
# =============================================================================

print("📡 MOBILITHEK DORMAGEN (Sensor.community)")
print("-" * 80)

# Get sensors near Dormagen from current API
print("Step 1: Finding active sensors in Dormagen...")

try:
    url = "https://data.sensor.community/airrohr/v1/filter/area=51.0946,6.8407,5"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    current_data = response.json()
    
    # Extract unique sensor IDs
    sensor_ids = set()
    for sensor_data in current_data:
        sensor_id = sensor_data.get('sensor', {}).get('id')
        if sensor_id:
            sensor_ids.add(sensor_id)
    
    print(f"✓ Found {len(sensor_ids)} active sensors")
    print(f"  Sensor IDs: {list(sensor_ids)[:5]}..." if len(sensor_ids) > 5 else f"  Sensor IDs: {list(sensor_ids)}")
    
except Exception as e:
    print(f"✗ Error finding sensors: {e}")
    sensor_ids = []

# Download historical data from sensor.community archive
print("\nStep 2: Downloading historical data (last 7 days)...")

all_dormagen_data = []
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

for sensor_id in list(sensor_ids)[:3]:  # Limit to first 3 sensors for speed
    print(f"\n  Downloading sensor {sensor_id}...")
    
    for day_offset in range(7):
        date = end_date - timedelta(days=day_offset)
        date_str = date.strftime('%Y-%m-%d')
        
        # Try different sensor types (SDS011 for PM, BME280 for temp/humidity)
        for sensor_type in ['sds011', 'bme280', 'dht22']:
            try:
                archive_url = f"https://archive.sensor.community/{date_str}/{date_str}_{sensor_type}_sensor_{sensor_id}.csv"
                
                df = pd.read_csv(archive_url, sep=';', on_bad_lines='skip')
                df['sensor_id'] = sensor_id
                df['sensor_type'] = sensor_type
                df['date'] = date_str
                all_dormagen_data.append(df)
                
                print(f"    ✓ {date_str} ({sensor_type}): {len(df)} records")
                time.sleep(0.5)  # Be nice to the server
                break  # Found data for this day
                
            except Exception:
                continue  # Try next sensor type

if all_dormagen_data:
    dormagen_df = pd.concat(all_dormagen_data, ignore_index=True)
    output_file = 'data/historical/mobilithek_dormagen_7days.csv'
    dormagen_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Mobilithek Dormagen data saved!")
    print(f"  File: {output_file}")
    print(f"  Records: {len(dormagen_df)}")
    print(f"  Columns: {list(dormagen_df.columns)[:8]}...")
else:
    print("\n⚠ No historical data found. Generating sample data...")
    
    # Generate sample data if download fails
    dates = pd.date_range(start=start_date, end=end_date, freq='H')
    sample_data = {
        'timestamp': dates,
        'P1': [18 + i%10 for i in range(len(dates))],  # PM10
        'P2': [12 + i%8 for i in range(len(dates))],   # PM2.5
        'temperature': [9 + (i%24)/4 for i in range(len(dates))],
        'humidity': [75 + (i%24) for i in range(len(dates))],
        'sensor_id': ['sample'] * len(dates),
        'location': ['Dormagen'] * len(dates)
    }
    dormagen_df = pd.DataFrame(sample_data)
    output_file = 'data/historical/mobilithek_dormagen_7days_sample.csv'
    dormagen_df.to_csv(output_file, index=False)
    
    print(f"  Sample data saved: {output_file}")

# =============================================================================
# 2. OPEN-METEO EGYPT (Cairo)
# =============================================================================

print("\n" + "="*80)
print("🌍 OPEN-METEO EGYPT (Cairo)")
print("-" * 80)

try:
    # Open-Meteo Archive API
    archive_url = "https://archive-api.open-meteo.com/v1/archive"
    
    end_date_str = datetime.now().strftime('%Y-%m-%d')
    start_date_str = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    params = {
        'latitude': 30.0444,
        'longitude': 31.2357,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'hourly': 'temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m',
        'timezone': 'Africa/Cairo'
    }
    
    print(f"Downloading Cairo weather data ({start_date_str} to {end_date_str})...")
    
    response = requests.get(archive_url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    hourly = data.get('hourly', {})
    
    # Create DataFrame
    egypt_df = pd.DataFrame({
        'timestamp': hourly['time'],
        'temperature_2m': hourly['temperature_2m'],
        'relative_humidity_2m': hourly['relative_humidity_2m'],
        'pressure_msl': hourly['pressure_msl'],
        'wind_speed_10m': hourly['wind_speed_10m'],
        'wind_direction_10m': hourly['wind_direction_10m'],
        'location': 'Cairo, Egypt',
        'source': 'Open-Meteo Archive'
    })
    
    output_file = 'data/historical/openmeteo_egypt_7days.csv'
    egypt_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Open-Meteo Egypt data saved!")
    print(f"  File: {output_file}")
    print(f"  Records: {len(egypt_df)}")
    print(f"  Date range: {egypt_df['timestamp'].min()} to {egypt_df['timestamp'].max()}")
    
    # Show sample
    print(f"\n  Sample data:")
    print(egypt_df[['timestamp', 'temperature_2m', 'relative_humidity_2m']].head(3).to_string(index=False))
    
except Exception as e:
    print(f"✗ Error downloading Egypt data: {e}")
    print("  Using sample data instead...")
    
    # Generate sample data
    dates = pd.date_range(start=start_date, end=end_date, freq='H')
    sample_data = {
        'timestamp': dates,
        'temperature_2m': [20 + i%15 for i in range(len(dates))],
        'relative_humidity_2m': [50 + i%30 for i in range(len(dates))],
        'pressure_msl': [1015 + i%10 for i in range(len(dates))],
        'wind_speed_10m': [5 + i%10 for i in range(len(dates))],
        'location': ['Cairo, Egypt'] * len(dates),
        'source': ['Sample Data'] * len(dates)
    }
    egypt_df = pd.DataFrame(sample_data)
    output_file = 'data/historical/openmeteo_egypt_7days_sample.csv'
    egypt_df.to_csv(output_file, index=False)
    
    print(f"  Sample data saved: {output_file}")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*80)
print("✓ DOWNLOAD COMPLETE")
print("="*80)

print("\nFiles saved in data/historical/:")
for file in os.listdir('data/historical'):
    filepath = os.path.join('data/historical', file)
    size_kb = os.path.getsize(filepath) / 1024
    print(f"  - {file} ({size_kb:.1f} KB)")

print("\n" + "="*80 + "\n")
