#!/usr/bin/env python3
"""
Generate Location Map (Karten)
Shows all sensor locations on an interactive map
"""

import folium
from folium import plugins
import pandas as pd

print("\n" + "="*80)
print("GENERATING LOCATION MAP - MIKROKLIMA HAMBURG")
print("="*80 + "\n")

# =============================================================================
# SENSOR LOCATIONS
# =============================================================================

sensors = {
    # German Sensors
    'Mobilithek Dormagen': {
        'lat': 51.0946,
        'lon': 6.8407,
        'type': 'Air Quality',
        'status': 'REAL',
        'color': 'green',
        'icon': 'cloud',
        'data': '11,139 records (PM10, PM2.5, Temp)'
    },
    'OpenSenseMap Hamburg': {
        'lat': 53.58121,
        'lon': 9.830826,
        'type': 'Weather Station',
        'status': 'CODE READY',
        'color': 'orange',
        'icon': 'thermometer',
        'data': 'Simulated (needs active box)'
    },
    'DWD Hamburg-Fuhlsbüttel': {
        'lat': 53.6332,
        'lon': 9.9881,
        'type': 'Official Weather',
        'status': 'MOCK',
        'color': 'blue',
        'icon': 'cloud-sun',
        'data': 'Mock data (7 measurements)'
    },
    'UDP Osnabrück': {
        'lat': 52.2799,
        'lon': 8.0472,
        'type': 'Microclimate',
        'status': 'MOCK',
        'color': 'blue',
        'icon': 'tree',
        'data': 'Mock data (4 measurements)'
    },
    
    # International Sensors
    'Open-Meteo Cairo': {
        'lat': 30.0444,
        'lon': 31.2357,
        'type': 'Weather API',
        'status': 'REAL',
        'color': 'green',
        'icon': 'globe',
        'data': '192 records (Temp, Humidity, Pressure, Wind)'
    },
    'Tunisia (Mock)': {
        'lat': 36.8065,
        'lon': 10.1815,
        'type': 'Weather Station',
        'status': 'MOCK',
        'color': 'blue',
        'icon': 'cloud',
        'data': 'Mock data (5 measurements)'
    }
}

print("📍 Sensor Locations:")
print("-" * 80)
for name, info in sensors.items():
    status_symbol = "🟢" if info['status'] == 'REAL' else "🟠" if info['status'] == 'CODE READY' else "🔵"
    print(f"{status_symbol} {name:<30} ({info['lat']:.4f}, {info['lon']:.4f}) - {info['status']}")

# =============================================================================
# CREATE MAP
# =============================================================================

print("\n🗺️  Creating interactive map...")

# Center map on Europe/North Africa (between Germany and Egypt)
center_lat = 45.0
center_lon = 15.0

# Create map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=4,
    tiles='OpenStreetMap'
)

# Add title
title_html = '''
<div style="position: fixed; 
            top: 10px; left: 50px; width: 400px; height: 90px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:14px; padding: 10px">
<b>Mikroklima Hamburg - IoT Project</b><br>
🟢 Real Data Sources<br>
🟠 Code Ready (needs configuration)<br>
🔵 Mock Data (demonstration)
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Add markers for each sensor
for name, info in sensors.items():
    # Create popup HTML
    popup_html = f"""
    <div style="width: 250px;">
        <h4>{name}</h4>
        <b>Type:</b> {info['type']}<br>
        <b>Status:</b> {info['status']}<br>
        <b>Location:</b> {info['lat']:.4f}, {info['lon']:.4f}<br>
        <b>Data:</b> {info['data']}
    </div>
    """
    
    # Add marker
    folium.Marker(
        location=[info['lat'], info['lon']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=name,
        icon=folium.Icon(color=info['color'], icon=info['icon'], prefix='fa')
    ).add_to(m)
    
    # Add circle to highlight area
    folium.Circle(
        location=[info['lat'], info['lon']],
        radius=50000 if 'Germany' in name or 'Dormagen' in name or 'Hamburg' in name or 'Osnabrück' in name else 100000,
        color=info['color'],
        fill=True,
        opacity=0.3
    ).add_to(m)

# Add Germany region
germany_bounds = [[47.3, 5.9], [55.1, 15.0]]
folium.Rectangle(
    bounds=germany_bounds,
    color='gray',
    fill=False,
    weight=2,
    dash_array='5'
).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; right: 50px; width: 200px; height: 140px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:12px; padding: 10px">
<b>Data Sources</b><br>
<i class="fa fa-map-marker fa-2x" style="color:green"></i> Real Data<br>
<i class="fa fa-map-marker fa-2x" style="color:orange"></i> Ready<br>
<i class="fa fa-map-marker fa-2x" style="color:blue"></i> Mock Data<br>
<br>
<b>Total:</b> 6 sources<br>
<b>Real:</b> 2 sources
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Add fullscreen button
plugins.Fullscreen().add_to(m)

# Save map
output_file = 'sensor_locations_map.html'
m.save(output_file)

print(f"✓ Map created: {output_file}")

# =============================================================================
# STATISTICS
# =============================================================================

print("\n📊 Map Statistics:")
print("-" * 80)

real_count = sum(1 for s in sensors.values() if s['status'] == 'REAL')
ready_count = sum(1 for s in sensors.values() if s['status'] == 'CODE READY')
mock_count = sum(1 for s in sensors.values() if s['status'] == 'MOCK')

print(f"Total sensors: {len(sensors)}")
print(f"  🟢 Real data: {real_count}")
print(f"  🟠 Code ready: {ready_count}")
print(f"  🔵 Mock data: {mock_count}")

print(f"\nCoverage:")
print(f"  Germany: 4 sensors (Dormagen, Hamburg, Fuhlsbüttel, Osnabrück)")
print(f"  International: 2 sensors (Egypt, Tunisia)")

print("\n" + "="*80)
print("✓ MAP GENERATION COMPLETE")
print("="*80)
print(f"\nOpen the map in your browser:")
print(f"  open {output_file}")
print("\n" + "="*80 + "\n")
